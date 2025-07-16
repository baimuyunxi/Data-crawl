import datetime
import logging
import time

import pandas as pd
from DrissionPage import Chromium

from db.pgDatabase import OperatePgsql
from util.hw_util import query_data, query_zun_old, select_hunan_province, select_time_province

# 配置日志记录器
logger = logging.getLogger(__name__)

xp = OperatePgsql()


def convert_percentage_to_numeric(value):
    """
    将百分比字符串转换为数值
    例如: "86.25%" -> 86.25
    如果值为None或无效，返回None
    """
    if pd.isna(value) or value is None:
        return None

    if isinstance(value, str):
        # 移除百分号并转换为浮点数
        if value.endswith('%'):
            try:
                return float(value.rstrip('%'))
            except ValueError:
                return None
        else:
            try:
                return float(value)
            except ValueError:
                return None

    return float(value) if not pd.isna(value) else None


def safe_convert_to_int(value):
    """
    安全地将值转换为整数
    如果值为None或无效，返回None
    """
    if pd.isna(value) or value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def process_single_date_data(result_df):
    """
    处理单个日期的数据，进行类型转换和清理
    """
    if result_df is None or result_df.empty:
        return None

    # 处理 p_day_id
    if 'p_day_id' in result_df.columns:
        result_df['p_day_id'] = result_df['p_day_id'].astype(str)

    # 处理 artCallinCt - 转换为整数类型，保持None值
    if 'artCallinCt' in result_df.columns:
        result_df['artCallinCt'] = result_df['artCallinCt'].apply(safe_convert_to_int)

    # 处理百分比字段 - 转换为数值类型，保持None值
    percentage_columns = ['conn15Rate', 'onceRate', 'artConnRt']

    for col in percentage_columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].apply(convert_percentage_to_numeric)

    # 入库前删除值为None的列
    columns_to_drop = []
    for col in result_df.columns:
        if result_df[col].iloc[0] is None:
            columns_to_drop.append(col)

    if columns_to_drop:
        logger.info(f"删除None值列: {columns_to_drop}")
        result_df = result_df.drop(columns=columns_to_drop)

    return result_df


def main():
    # 获取当前日期
    today = datetime.date.today()

    # 获取昨天日期
    yesterday = today - datetime.timedelta(days=1)

    now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
    logger.info(f"查询日期: {now_today}")

    # 连接浏览器
    browser = Chromium()

    # 获取条件标签页
    tab = browser.get_tab(title='10000号运营管理平台')

    logger.info('刷新浏览器tab页')
    tab.refresh()
    time.sleep(5)

    # 检查main元素并点击SVG图标
    if tab.ele('tag:main@class=el-main'):
        icon_span = tab.ele('tag:span@class=icon-tabs')
        if icon_span:
            icon_span.click()
            logger.info("成功点击了图标")
        else:
            tab.ele('xpath://div[@id="main"]/div[3]/section[1]/section[1]/aside[1]/div[1]/div[1]/ul[1]/li[6]').click()
            logger.info("未找到图标元素")
    else:
        logger.info("跳过点击侧边栏收缩！")

    # 点击 话务运营重点指标 栏
    route_zdzb = tab.ele('tag:span@title=话务运营重点指标')
    if route_zdzb:
        route_zdzb.click()
        logger.info("点击话务运营重点指标")
        time.sleep(2)

        # 执行地区选择
        if select_hunan_province(tab):
            logger.info("地区选择完成")
            time.sleep(2)

            # 执行日期选择
            if select_time_province(tab, now_today):
                # 点击搜索按钮
                search_button = tab.ele('xpath://button[@id="searchColClass-search"]/span[1]')
                if search_button:
                    search_button.click()
                    logger.info("完成指定日期查询！")
                    time.sleep(2)  # 等待页面加载

                    # 获取数据
                    try:
                        # 获取语音人工呼入量（artCallinCt)、语音客服15s接通率（conn15Rate）、10000号人工一解率（onceRate)
                        data = query_data(tab)
                        logger.info("成功获取基础数据")

                        # 获取尊老用户数据
                        data_zl = query_zun_old(tab)
                        logger.info("成功获取尊老用户数据")

                        # 生成日期字段
                        p_day_id = yesterday.strftime('%Y%m%d')  # 格式：20250621

                        # 合并数据为一行
                        if data is not None and data_zl is not None:
                            # 初始化结果字典
                            merged_data = {
                                'p_day_id': p_day_id,
                            }

                            # 处理基础数据
                            if isinstance(data, pd.DataFrame):
                                # 将DataFrame转换为字典，合并所有非空值
                                for col in data.columns:
                                    non_null_values = data[col].dropna()
                                    if not non_null_values.empty:
                                        merged_data[col] = non_null_values.iloc[0]
                            elif isinstance(data, dict):
                                merged_data.update(data)

                            # 处理尊老用户数据
                            if isinstance(data_zl, pd.DataFrame):
                                # 将DataFrame转换为字典，合并所有非空值
                                for col in data_zl.columns:
                                    non_null_values = data_zl[col].dropna()
                                    if not non_null_values.empty:
                                        merged_data[col] = non_null_values.iloc[0]
                            elif isinstance(data_zl, dict):
                                merged_data.update(data_zl)

                            # 转换为单行DataFrame
                            final_result = pd.DataFrame([merged_data])
                            logger.info("数据合并完成（单行格式）")

                            # 处理数据类型转换和清理
                            processed_result = process_single_date_data(final_result)

                            if processed_result is not None:
                                logger.info("\n=== 数据处理后结果 ===")
                                logger.info(str(processed_result))

                                # 导入数据库
                                try:
                                    xp.insert_data(processed_result, 'central_indicator_monitor_data')
                                    logger.info("\n=== 数据库插入成功 ===")
                                    return processed_result
                                except Exception as e:
                                    logger.error(f"\n=== 数据库插入失败 ===")
                                    logger.error(f"错误信息: {e}")
                                    return None
                            else:
                                logger.error("数据处理失败")
                                return None
                        else:
                            logger.warning("警告：部分数据获取失败")
                            return None

                    except Exception as e:
                        logger.error(f"数据获取过程中发生错误: {e}")
                        return None
                else:
                    logger.error("未找到搜索按钮")
                    return None
            else:
                logger.error("日期选择失败！终止执行")
                return None
        else:
            logger.error("地区选择失败！终止执行")
            return None
    else:
        logger.error("未找到话务运营重点指标，终止执行")
        return None


if __name__ == "__main__":
    # 执行主函数
    result = main()

    if result is not None:
        logger.info("\n=== 执行成功 ===")
        logger.info(f"成功处理了 1 条记录")
        logger.info(str(result))
    else:
        logger.error("\n=== 执行失败 ===")
        logger.error("未能成功获取数据")
