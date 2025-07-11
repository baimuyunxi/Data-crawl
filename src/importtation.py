import datetime
import time

import pandas as pd
from DrissionPage import Chromium

from db.pgDatabase import OperatePgsql

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
        print(f"删除None值列: {columns_to_drop}")
        result_df = result_df.drop(columns=columns_to_drop)

    return result_df


def main():
    # 获取当前日期
    today = datetime.date.today()

    # 获取昨天日期
    yesterday = today - datetime.timedelta(days=1)

    now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
    print(f"查询日期: {now_today}")
    row_data = {}

    # 连接浏览器
    browser = Chromium()

    print('开始获取文字客服服务量与接通率')

    # 获取条件标签页
    tab = browser.get_tab(title='IM会话服务量接通率多维分析')

    print('刷新浏览器tab页')
    tab.refresh()
    time.sleep(30)

    try:
        # 文字客服呼入量(wordCallinCt)
        element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[2]')
        if element:
            row_data['wordCallinCt'] = element.text.strip()
            print(f"获取到 文字客服呼入量 值: {row_data['wordCallinCt']}")
        else:
            print("未找到 文字客服呼入量 元素")
            row_data['wordCallinCt'] = None

        # 文字客服5分钟接通率(word5Rate)
        element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[11]')
        if element:
            row_data['word5Rate'] = element.text.strip()
            print(f"获取到 文字客服5分钟接通率 值: {row_data['word5Rate']}")
        else:
            print("未找到 文字客服5分钟接通率 元素")
            row_data['word5Rate'] = None

    except Exception as e:
        print(f"文字客服数据获取出错: {e}")
        return pd.DataFrame()

    print('开始获取远程柜台服务量与接通率')

    # 获取条件标签页
    tab = browser.get_tab(title='远程柜台服务量接通率多维分析')

    print('刷新浏览器tab页')
    tab.refresh()
    time.sleep(30)

    try:
        # 远程柜台呼入量(farCabinetCt)
        element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[2]')
        if element:
            row_data['farCabinetCt'] = element.text.strip()
            print(f"获取到 远程柜台呼入量 值: {row_data['farCabinetCt']}")
        else:
            print("未找到 远程柜台呼入量 元素")
            row_data['farCabinetCt'] = None

        # 远程柜台25秒接通率(farCabinetRate)
        element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[6]')
        if element:
            row_data['farCabinetRate'] = element.text.strip()
            print(f"获取到 远程柜台25秒接通率 值: {row_data['farCabinetRate']}")
        else:
            print("未找到 远程柜台25秒接通率 元素")
            row_data['farCabinetRate'] = None

    except Exception as e:
        print(f"远程柜台数据获取出错: {e}")
        return pd.DataFrame()

    print('获取10000号重复来电率')
    # 获取条件标签页
    tab = browser.get_tab(title='高频呼入统计报表')

    print('刷新浏览器tab页')
    tab.refresh()
    time.sleep(30)

    print('选择10000号接入号')
    tab.ele('xpath://span[@id="undefined_4_switch"]').click()
    time.sleep(5)
    print('开始拖拽')
    tab.actions.hold('xpath://span[@id="undefined_20_span"]/span[1]').release(
        'xpath://div[contains(@class,"left ui-droppable")]')
    tab.actions.release()
    time.sleep(20)

    try:
        # 10000号重复来电率(repeatRate)
        element = tab.ele('xpath://table[1]/tbody[1]/tr[2]/td[7]')
        if element:
            row_data['repeatRate'] = element.text.strip()
            print(f"获取到 10000号重复来电率 值: {row_data['repeatRate']}")
        else:
            print("未找到 10000号重复来电率 元素")
            row_data['repeatRate'] = None

    except Exception as e:
        print(f"10000号重复来电率数据获取出错: {e}")
        return pd.DataFrame()

    data = pd.DataFrame([row_data])

    # 生成日期字段
    p_day_id = yesterday.strftime('%Y%m%d')

    # 合并数据为一行
    if data is not None:
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

        # 转换为单行DataFrame
        final_result = pd.DataFrame([merged_data])
        print("数据合并完成（单行格式）")

        # 处理数据类型转换和清理
        processed_result = process_single_date_data(final_result)

        if processed_result is not None:
            print("\n=== 数据处理后结果 ===")
            print(processed_result)

            # 导入数据库
            try:
                xp.insert_data(processed_result, 'central_indicator_monitor_data')
                print("\n=== 数据库插入成功 ===")
                return processed_result
            except Exception as e:
                print(f"\n=== 数据库插入失败 ===")
                print(f"错误信息: {e}")
                return None


if __name__ == "__main__":
    # 执行主函数
    main()
