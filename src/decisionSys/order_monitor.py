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
    percentage_columns = ['ordersolve', 'orderdeclaration', 'orderrepeat',
                          'moveorder', 'bandorder', 'tsordersolve',
                          'cxordersolve', 'gzordersolve', 'tsordertimerat',
                          'tsorderoverrat', 'ydorderoverrat', 'kdorderoverrat',
                          'kdonlinepre', 'kdorderpre']

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


def get_table_value_by_row_column(report_tab, row_name, column_name):
    """
    根据行名称和列名称获取表格中交叉位置的数值
    适配多级表头的复杂表格

    Args:
        report_tab: 报表标签页对象
        row_name: 行名称（例如："20250813" 或 "合计"）
        column_name: 列名称（例如："工单总量"、"一级预处理率"等）

    Returns:
        str: 交叉位置的数值，如果未找到返回None
    """
    try:
        # 1. 定位到表格 - 尝试多种选择器
        table = None
        selectors = [
            'css:.rows-height-counter',
            'xpath://tbody[@class="rows-height-counter"]',
            'xpath://table//tbody',
            'css:tbody'
        ]

        for selector in selectors:
            table = report_tab.ele(selector)
            if table:
                logger.info(f"使用选择器 '{selector}' 成功定位到表格")
                break

        if table is None:
            logger.error("未找到表格元素")
            return None

        logger.info(f"成功定位到表格，开始查找行名称: {row_name}, 列名称: {column_name}")

        # 2. 获取所有行
        rows = table.eles('tag:tr')
        if not rows:
            logger.error("表格中未找到任何行")
            return None

        logger.info(f"找到 {len(rows)} 行数据")

        # 3. 分析表头结构，找到列索引
        column_index = None

        # 遍历所有表头行来查找列名
        for header_row_idx in range(min(3, len(rows))):  # 最多检查前3行作为表头
            header_row = rows[header_row_idx]
            header_cells = header_row.eles('tag:td')

            for i, cell in enumerate(header_cells):
                cell_text = cell.text.strip()
                logger.debug(f"表头第{header_row_idx}行第{i}列: '{cell_text}'")

                # 检查是否匹配列名
                if cell_text == column_name:
                    column_index = i
                    logger.info(f"在第{header_row_idx}行找到列名称 '{column_name}' 在第 {i} 列")
                    break

            if column_index is not None:
                break

        # 如果还未找到，尝试模糊匹配
        if column_index is None:
            logger.warning(f"精确匹配未找到列名称 '{column_name}'，尝试模糊匹配")
            for header_row_idx in range(min(3, len(rows))):
                header_row = rows[header_row_idx]
                header_cells = header_row.eles('tag:td')

                for i, cell in enumerate(header_cells):
                    cell_text = cell.text.strip()
                    if column_name in cell_text or cell_text in column_name:
                        column_index = i
                        logger.info(f"模糊匹配找到列名称 '{cell_text}' 在第 {i} 列")
                        break

                if column_index is not None:
                    break

        if column_index is None:
            logger.error(f"未找到列名称: {column_name}")
            # 打印所有表头信息用于调试
            for header_row_idx in range(min(3, len(rows))):
                header_row = rows[header_row_idx]
                header_cells = header_row.eles('tag:td')
                headers = [cell.text.strip() for cell in header_cells]
                logger.error(f"第{header_row_idx}行表头: {headers}")
            return None

        # 4. 查找数据行（从第3行开始，因为可能有多级表头）
        data_start_row = 2  # 默认从第3行开始查找数据

        for row_idx in range(data_start_row, len(rows)):
            row = rows[row_idx]
            cells = row.eles('tag:td')

            # 检查第一列是否包含行名称（通常日期在第一列）
            if cells:
                first_cell_text = cells[0].text.strip()
                logger.debug(f"第{row_idx}行第一列: '{first_cell_text}'")

                if first_cell_text == row_name:
                    logger.info(f"找到行名称 '{row_name}' 在第 {row_idx} 行")

                    # 获取指定列的数值
                    if column_index < len(cells):
                        target_cell = cells[column_index]

                        # 尝试获取链接内的文本（如果存在）
                        link_span = target_cell.ele('xpath:.//span[@class="linkspan"]')
                        if link_span:
                            value = link_span.text.strip()
                        else:
                            value = target_cell.text.strip()

                        logger.info(f"成功获取交叉位置数值: '{value}'")
                        return value
                    else:
                        logger.error(f"指定列索引 {column_index} 超出该行的列数 {len(cells)}")
                        return None

        logger.error(f"未找到行名称: {row_name}")
        return None

    except Exception as e:
        logger.error(f"获取表格数值时出错: {e}")
        return None


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
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[4]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                ordersolve = get_table_value_by_row_column(tab1, "合计", '解决率（员工点选）')
                if ordersolve is not None:
                    print(f"获取到 最严工单问题解决率 值: {ordersolve}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'ordersolve', ordersolve)
                else:
                    logger.warning("未找到 最严工单问题解决率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 客户工单执行情况统计表-预办结 出错:{e}")


# 投诉处理重复率 投诉工单逾限且催单率
def get_order_duplicate():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '重复工单-同一问题')

            if success:
                logger.info("成功打开 重复工单-同一问题 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='重复工单-同一问题')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[18]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[19]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-FORMSUBMIT0_C"]/div/em/button').click()
                time.sleep(5)

                orderrepeat = get_table_value_by_row_column(tab1, "合计", '重复工单率')
                if orderrepeat is not None:
                    print(f"获取到 投诉处理重复率 值: {orderrepeat}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'orderrepeat', orderrepeat)
                else:
                    logger.warning("未找到 投诉处理重复率 元素")

                tsorderoverrat = get_table_value_by_row_column(tab1, "合计", '逾限后催单率')
                if tsorderoverrat is not None:
                    print(f"获取到 投诉工单逾限且催单率 值: {tsorderoverrat}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'tsorderoverrat', tsorderoverrat)
                else:
                    logger.warning("未找到 投诉工单逾限且催单率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 重复工单-同一问题 出错:{e}")


# 移动故障工单重复率（万号办结）   宽带故障工单重复率（万号办结）
def get_order_wh_been():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '重复工单')

            if success:
                logger.info("成功打开 重复工单 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='重复工单报表')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[18]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[19]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)
                element_name = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element_name.input('移动故障', clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                moveorder = get_table_value_by_row_column(tab1, "省客服中心", '重复工单率')
                if moveorder is not None:
                    print(f"获取到 移动故障工单重复率（万号办结） 值: {moveorder}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'moveorder', moveorder)
                else:
                    logger.warning("未找到 移动故障工单重复率（万号办结） 元素")

                time.sleep(3)
                element_name = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element_name.input('宽带故障', clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                bandorder = get_table_value_by_row_column(tab1, "省客服中心", '重复工单率')
                if bandorder is not None:
                    print(f"获取到 宽带故障工单重复率（万号办结） 值: {bandorder}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'bandorder', bandorder)
                else:
                    logger.warning("未找到 宽带故障工单重复率（万号办结） 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 重复工单 出错:{e}")


# 移动故障工单逾限且催单率
def get_order_yd():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '重复工单-移动故障')

            if success:
                logger.info("成功打开 重复工单-移动故障 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='重复工单报表-移动')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[18]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[19]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                element_name = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element_name.input('移动故障', clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                ydorderoverrat = get_table_value_by_row_column(tab1, "省客服中心", '催单率（48小时）')
                if ydorderoverrat is not None:
                    print(f"获取到 移动故障工单逾限且催单率 值: {ydorderoverrat}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'ydorderoverrat', ydorderoverrat)
                else:
                    logger.warning("未找到 移动故障工单逾限且催单率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 重复工单-移动故障 出错:{e}")


# 宽带故障工单逾限且催单率
def get_order_kd():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '重复工单-宽带故障')

            if success:
                logger.info("成功打开 重复工单-宽带故障 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='重复工单报表-宽带')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[18]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[19]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                element_name = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element_name.input('宽带故障', clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                kdorderoverrat = get_table_value_by_row_column(tab1, "省客服中心", '催单率（48小时）')
                if kdorderoverrat is not None:
                    print(f"获取到 宽带故障工单逾限且催单率 值: {kdorderoverrat}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'kdorderoverrat', kdorderoverrat)
                else:
                    logger.warning("未找到 宽带故障工单逾限且催单率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 重复工单-宽带故障 出错:{e}")


# 宽带在线预处理率
def get_order_kd_online():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '宽带预处理(新)')

            if success:
                logger.info("成功打开 宽带预处理(新) 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='宽带故障预处理(新)')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[4]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[13]/span').click()
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                kdonlinepre = get_table_value_by_row_column(tab1, "合计", '整体预处理率')
                if kdonlinepre is not None:
                    print(f"获取到 宽带在线预处理率 值: {kdonlinepre}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'kdonlinepre', kdonlinepre)
                else:
                    logger.warning("未找到 宽带在线预处理率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 宽带预处理(新) 出错:{e}")


# 宽带故障预处理及时率
def get_order_kd_pre():
    tab, p_day_id, browser = main_browser()

    if tab is not None:
        try:
            success = search_and_click_report(tab, '宽带故障处理及时率')

            if success:
                logger.info("成功打开 宽带故障处理及时率 报表")
                # 等待报表页面加载完成
                time.sleep(5)

                tab1 = browser.get_tab(title='宽带故障处理及时率')

                element = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[2]/div[1]/input')
                element.input(p_day_id, clear=True)
                time.sleep(3)
                element_end = tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[4]/div[1]/input')
                element_end.input(p_day_id, clear=True)
                time.sleep(3)

                tab1.ele('xpath://*[@id="id_container"]/div[1]/div[1]/div[3]/div/div[11]/span').click()
                time.sleep(3)

                tab1.ele('xpath://*[@id="fr-btn-查询"]/div/em/button').click()
                time.sleep(5)

                kdorderpre = get_table_value_by_row_column(tab1, "合计", '客服中心1小时及时率')
                if kdorderpre is not None:
                    print(f"获取到 宽带故障预处理及时率 值: {kdorderpre}")

                    # 立即入库
                    insert_indicator_data(p_day_id, 'kdorderpre', kdorderpre)
                else:
                    logger.warning("未找到 宽带故障预处理及时率 元素")

                tab1.close()

            else:
                logger.error("未能找到并点击目标报表")

        except Exception as e:
            print(f"打开 宽带预处理(新) 出错:{e}")


if __name__ == "__main__":
    # 执行主函数
    get_strictest_work_oder()
    get_order_duplicate()
    get_order_wh_been()
    get_order_yd()
    get_order_kd()
    get_order_kd_online()
    get_order_kd_pre()
