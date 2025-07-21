import datetime
import logging
import time

import pandas as pd
from DrissionPage import Chromium

from src.db.pgDatabase import OperatePgsql

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


def process_single_date_data(result_df):
    """
    处理单个日期的数据，进行类型转换和清理
    """
    if result_df is None or result_df.empty:
        return None

    # 处理 p_day_id
    if 'p_day_id' in result_df.columns:
        result_df['p_day_id'] = result_df['p_day_id'].astype(str)

    # 处理百分比字段 - 转换为数值类型，保持None值
    percentage_columns = ['word5Rate', 'farCabinetRate', 'repeatRate']

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


def insert_indicator_data(p_day_id, field_name, field_value):
    """
    插入单个指标数据到数据库
    """
    if field_value is None:
        logger.warning(f"指标 {field_name} 值为None，跳过入库")
        return False

    # 构造单行数据
    data_dict = {
        'p_day_id': p_day_id,
        field_name: field_value
    }

    # 转换为DataFrame
    df = pd.DataFrame([data_dict])

    # 处理数据类型转换和清理
    processed_df = process_single_date_data(df)

    if processed_df is not None and not processed_df.empty:
        try:
            xp.insert_data(processed_df, 'central_indicator_monitor_data')
            logger.info(f"指标 {field_name} 入库成功，值: {field_value}")
            return True
        except Exception as e:
            logger.error(f"指标 {field_name} 入库失败: {e}")
            return False
    else:
        logger.warning(f"指标 {field_name} 数据处理后为空，跳过入库")
        return False


def main():
    # 获取当前日期
    today = datetime.date.today()

    # 获取昨天日期
    yesterday = today - datetime.timedelta(days=1)

    now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
    logger.info(f"查询日期: {now_today}")

    # 生成日期字段
    p_day_id = yesterday.strftime('%Y%m%d')

    # 连接浏览器
    browser = Chromium()

    logger.info('开始获取文字客服服务量与接通率')

    # 获取条件标签页
    try:
        tab = browser.get_tab(title='IM会话服务量接通率多维分析')
        if tab is None:
            logger.warning("未找到 IM会话服务量接通率多维分析 标签页，跳过该部分")
        else:
            logger.info('刷新浏览器tab页')
            tab.refresh()
            time.sleep(30)
    except Exception as e:
        logger.error(f"获取 IM会话服务量接通率多维分析 标签页失败: {e}，跳过该部分")
        tab = None

    if tab is not None:
        try:
            # 文字客服呼入量(wordCallinCt)
            element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[2]')
            if element:
                wordCallinCt = element.text.strip()
                logger.info(f"获取到 文字客服呼入量 值: {wordCallinCt}")
                # 立即入库
                insert_indicator_data(p_day_id, 'wordCallinCt', wordCallinCt)
            else:
                logger.warning("未找到 文字客服呼入量 元素")

            # 文字客服5分钟接通率(word5Rate)
            element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[11]')
            if element:
                word5Rate = element.text.strip()
                logger.info(f"获取到 文字客服5分钟接通率 值: {word5Rate}")
                # 立即入库
                insert_indicator_data(p_day_id, 'word5Rate', word5Rate)
            else:
                logger.warning("未找到 文字客服5分钟接通率 元素")

        except Exception as e:
            logger.error(f"文字客服数据获取出错: {e}")

    logger.info('开始获取远程柜台服务量与接通率')

    # 获取条件标签页
    try:
        tab = browser.get_tab(title='远程柜台服务量接通率多维分析')
        if tab is None:
            logger.warning("未找到 远程柜台服务量接通率多维分析 标签页，跳过该部分")
        else:
            logger.info('刷新浏览器tab页')
            tab.refresh()
            time.sleep(30)
    except Exception as e:
        logger.error(f"获取 远程柜台服务量接通率多维分析 标签页失败: {e}，跳过该部分")
        tab = None

    if tab is not None:
        try:
            # 远程柜台呼入量(farCabinetCt)
            element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[2]')
            if element:
                farCabinetCt = element.text.strip()
                logger.info(f"获取到 远程柜台呼入量 值: {farCabinetCt}")
                # 立即入库
                insert_indicator_data(p_day_id, 'farCabinetCt', farCabinetCt)
            else:
                logger.warning("未找到 远程柜台呼入量 元素")

            # 远程柜台25秒接通率(farCabinetRate)
            element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[6]')
            if element:
                farCabinetRate = element.text.strip()
                logger.info(f"获取到 远程柜台25秒接通率 值: {farCabinetRate}")
                # 立即入库
                insert_indicator_data(p_day_id, 'farCabinetRate', farCabinetRate)
            else:
                logger.warning("未找到 远程柜台25秒接通率 元素")

        except Exception as e:
            logger.error(f"远程柜台数据获取出错: {e}")

    logger.info('获取10000号重复来电率')

    # 获取条件标签页
    try:
        tab = browser.get_tab(title='高频呼入统计报表')
        if tab is None:
            logger.warning("未找到 高频呼入统计报表 标签页，跳过该部分")
        else:
            logger.info('刷新浏览器tab页')
            tab.refresh()
            time.sleep(30)
    except Exception as e:
        logger.error(f"获取 高频呼入统计报表 标签页失败: {e}，跳过该部分")
        tab = None

    if tab is not None:
        try:
            logger.info('选择10000号接入号')
            tab.ele('xpath://span[@id="undefined_4_switch"]').click()
            time.sleep(5)
            logger.info('开始拖拽')
            tab.actions.hold('xpath://span[@id="undefined_20_span"]/span[1]').release(
                'xpath://div[contains(@class,"left ui-droppable")]')
            tab.actions.release()
            time.sleep(20)
            # 10000号重复来电率(repeatRate)
            element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[7]')
            if element:
                repeatRate = element.text.strip()
                logger.info(f"获取到 10000号重复来电率 值: {repeatRate}")
                # 立即入库
                insert_indicator_data(p_day_id, 'repeatRate', repeatRate)
            else:
                logger.warning("未找到 10000号重复来电率 元素")

        except Exception as e:
            logger.error(f"10000号重复来电率数据获取出错: {e}")


if __name__ == "__main__":
    # 执行主函数
    result = main()
