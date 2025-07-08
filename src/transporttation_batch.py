import datetime
import time

import pandas as pd
from DrissionPage import Chromium

from db.pgDatabase import OperatePgsql
from util.hw_util import query_data, query_zun_old, select_hunan_province, select_time_province

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
        print(f"删除None值列: {columns_to_drop}")
        result_df = result_df.drop(columns=columns_to_drop)

    return result_df


def main():
    # 获取当前日期
    today = datetime.date.today()

    # 获取昨天日期
    yesterday = today - datetime.timedelta(days=1)

    start_date = datetime.datetime.strptime("20250501", "%Y%m%d")
    end_date = datetime.datetime.strptime("20250530", "%Y%m%d")

    print(f"开始处理日期范围: {start_date.strftime('%Y%m%d')} 到 {end_date.strftime('%Y%m%d')}")

    # 连接浏览器
    browser = Chromium()

    # 用于存储所有处理成功的结果
    all_results = []
    failed_dates = []

    # 循环生成日期
    current_date = start_date
    while current_date <= end_date:
        datatime = current_date.strftime("%Y%m%d")
        print("------------------------" + datatime + "------------------------")
        now_today = current_date.strftime('%Y 年 %m 月 %d 日')

        try:
            # 获取条件标签页
            tab = browser.get_tab(title='10000号运营管理平台')

            print('刷新浏览器tab页')
            tab.refresh()
            time.sleep(5)

            # 检查main元素并点击SVG图标
            if tab.ele('tag:main@class=el-main'):
                icon_span = tab.ele('tag:span@class=icon-tabs')
                if icon_span:
                    icon_span.click()
                    print("成功点击了图标")
                else:
                    tab.ele(
                        'xpath://div[@id="main"]/div[3]/section[1]/section[1]/aside[1]/div[1]/div[1]/ul[1]/li[6]').click()
                    print("未找到图标元素")
            else:
                print("跳过点击侧边栏收缩！")

            # 点击 话务运营重点指标 栏
            route_zdzb = tab.ele('tag:span@title=话务运营重点指标')
            if route_zdzb:
                route_zdzb.click()
                print("点击话务运营重点指标")
                time.sleep(2)

                # 执行地区选择
                if select_hunan_province(tab):
                    print("地区选择完成")
                    time.sleep(2)

                    # 执行日期选择
                    if select_time_province(tab, now_today):
                        # 点击搜索按钮
                        search_button = tab.ele('xpath://button[@id="searchColClass-search"]/span[1]')
                        if search_button:
                            search_button.click()
                            print("完成指定日期查询！")
                            time.sleep(2)  # 等待页面加载

                            # 获取数据
                            try:
                                # 获取语音人工呼入量（artCallinCt)、语音客服15s接通率（conn15Rate）、10000号人工一解率（onceRate)
                                data = query_data(tab)
                                print("成功获取基础数据")

                                # 获取尊老用户数据
                                data_zl = query_zun_old(tab)
                                print("成功获取尊老用户数据")

                                # 生成日期字段 - 使用当前处理的日期而不是昨天
                                p_day_id = current_date.strftime('%Y%m%d')  # 格式：20250501

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
                                    single_day_result = pd.DataFrame([merged_data])
                                    print(f"数据合并完成（{datatime}）")

                                    # 处理数据类型转换和清理
                                    processed_result = process_single_date_data(single_day_result)

                                    if processed_result is not None:
                                        # 导入数据库
                                        try:
                                            xp.insert_data(processed_result, 'central_indicator_monitor_data')
                                            print(f"日期 {datatime} 数据库插入成功")
                                            all_results.append(processed_result)
                                        except Exception as e:
                                            print(f"日期 {datatime} 数据库插入失败: {e}")
                                            failed_dates.append(datatime)
                                    else:
                                        print(f"日期 {datatime} 数据处理失败")
                                        failed_dates.append(datatime)
                                else:
                                    print(f"警告：日期 {datatime} 部分数据获取失败")
                                    failed_dates.append(datatime)

                            except Exception as e:
                                print(f"日期 {datatime} 数据获取过程中发生错误: {e}")
                                failed_dates.append(datatime)
                        else:
                            print(f"日期 {datatime} 未找到搜索按钮")
                            failed_dates.append(datatime)
                    else:
                        print(f"日期 {datatime} 日期选择失败！")
                        failed_dates.append(datatime)
                else:
                    print(f"日期 {datatime} 地区选择失败！")
                    failed_dates.append(datatime)
            else:
                print(f"日期 {datatime} 未找到话务运营重点指标")
                failed_dates.append(datatime)

        except Exception as e:
            print(f"日期 {datatime} 处理过程中发生异常: {e}")
            failed_dates.append(datatime)

        # 移动到下一个日期
        current_date += datetime.timedelta(days=1)

        # 在日期之间添加短暂延迟，避免对服务器造成过大压力
        time.sleep(1)

    # 输出最终统计结果
    print("\n" + "=" * 50)
    print("=== 最终处理统计 ===")
    print(f"成功处理日期数量: {len(all_results)}")
    print(f"失败日期数量: {len(failed_dates)}")

    if failed_dates:
        print(f"失败的日期: {failed_dates}")

    if all_results:
        # 合并所有成功的结果
        final_combined_result = pd.concat(all_results, ignore_index=True)
        print(f"总共插入数据库记录数: {len(final_combined_result)}")
        return final_combined_result
    else:
        print("没有成功处理任何日期的数据")
        return None


if __name__ == "__main__":
    # 执行主函数
    result = main()

    if result is not None:
        print("\n=== 执行成功 ===")
        print(f"成功处理了 {len(result)} 条记录")
    else:
        print("\n=== 执行失败 ===")
        print("未能成功获取任何数据")
