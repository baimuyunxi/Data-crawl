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


def main_browser():
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

    logger.info('决策工单相关数据！')

    # 获取条件标签页
    try:
        tab = browser.get_tab(title='决策支持专家系统门户')
        if tab is None:
            logger.warning("未找到 决策支持专家系统门户 标签页，跳过该部分")
        else:
            logger.info('刷新浏览器tab页')
            # tab.refresh()
            time.sleep(10)
            tab.ele(
                'xpath://*[@id="root"]/div/section/section/main/div/div[3]/div/div[2]/div/span/span/span/button').click()
            return tab, p_day_id, browser
    except Exception as e:
        logger.error(f"获取 决策支持专家系统门户 标签页失败: {e}，跳过该部分")
        return None, None, None


def search_and_click_report(tab, search_text, target_text=None):
    """
    通用函数：搜索并点击指定的报表链接

    Args:
        tab: 浏览器标签页对象
        search_text: 在搜索框中输入的文本
        target_text: 要点击的链接文本，如果为None则使用search_text

    Returns:
        tuple: (是否成功, 新打开的标签页对象或None)
    """
    if target_text is None:
        target_text = search_text.strip()

    try:
        # 1. 在搜索框中输入搜索文本
        logger.info(f"搜索文本: {search_text}")
        search_input = tab.ele(
            'xpath://*[@id="root"]/div/section/section/main/div/div[3]/div[2]/div[2]/div/div/div[1]/div/div[2]/span/input')
        search_input.input(search_text, clear=True)

        time.sleep(2)
        tab.ele(
            'xpath://*[@id="root"]/div/section/section/main/div/div[3]/div[2]/div[2]/div/div/div[1]/div/div[2]/span/span').click()

        # 等待搜索结果加载
        time.sleep(5)

        # 2. 查找表格tbody元素
        tbody_xpath = 'xpath://*[@id="root"]/div/section/section/main/div/div[3]/div[2]/div[2]/div/div/div[2]/div/div/div/div/div/div/div/table/tbody'
        tbody = tab.ele(tbody_xpath, timeout=10)

        if tbody is None:
            logger.error("未找到表格tbody元素")
            return False

        # 3. 遍历所有行，查找匹配的链接
        rows = tbody.eles('tag:tr')
        logger.info(f"找到 {len(rows)} 行数据")

        for i, row in enumerate(rows, 1):
            try:
                # 查找第4列的链接元素 (td[4]/a)
                link_element = row.ele('xpath:./td[4]/a')
                if link_element:
                    link_text = link_element.text.strip()
                    logger.info(f"第{i}行链接文本: {link_text}")

                    # 检查是否匹配目标文本
                    if link_text == target_text:
                        logger.info(f"找到匹配链接: {target_text}，准备点击")

                        # 点击链接
                        link_element.click()
                        logger.info(f"成功点击链接: {target_text}")

                        # 等待新标签页打开
                        time.sleep(5)

                        return True

                else:
                    logger.debug(f"第{i}行未找到链接元素")
            except Exception as row_e:
                logger.warning(f"处理第{i}行时出错: {row_e}")
                continue

        logger.warning(f"未找到匹配的链接: {target_text}")
        return False

    except Exception as e:
        logger.error(f"搜索并点击报表时出错: {e}")
        return False


# 最严工单问题解决率
def get_strictest_work_oder():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '客户工单执行情况统计表-预办结')

            if success:
                logger.info("成功打开客户工单执行情况统计表-预办结报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='客户工单执行情况统计表-预办结')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element.input('20250811', clear=True)


            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 客户工单执行情况统计表-预办结 出错:{e}")


if __name__ == "__main__":
    # 执行主函数
    get_strictest_work_oder()
