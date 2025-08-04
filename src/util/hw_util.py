import datetime
import logging
import time

import pandas as pd

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
    percentage_columns = ['conn15Rate', 'onceRate', 'artConnRt', 'repeatRate']

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


# 处理地区选择
def select_hunan_province(tab):
    try:
        # 1. 检查是否已存在湖南省标签
        tags_container = tab.ele('css:.el-cascader__tags')
        if tags_container:
            existing_hunan = tags_container.ele('xpath:.//span[contains(text(), "湖南省")]', timeout=1)
            if existing_hunan:
                logger.info("湖南省标签已存在，跳过")
                return True

        # 2. 打开级联选择器
        cascader_input = tab.ele('css:.el-cascader .el-input__inner')
        if not cascader_input:
            logger.error("未找到级联选择器输入框")
            return False

        cascader_input.click()
        logger.info("打开级联选择器")
        time.sleep(2)

        # 3. 点击广东大区展开子菜单
        # 使用动态xpath，忽略随机ID
        guangdong_xpath = '//li[contains(@id,"cascader-menu-") and contains(@id,"-0-0")]/span[1]/span[1][text()="广东大区"]'
        guangdong_element = tab.eles(f'xpath:{guangdong_xpath}', timeout=3)

        for x in guangdong_element:
            logger.info(f'点击广东大区: {x.states.is_clickable}')
            if x.states.is_clickable:
                guangdong_element = x
                break
        if guangdong_element:
            guangdong_element.click()
            logger.info("点击广东大区，展开子菜单")
            time.sleep(1.5)
        else:
            logger.error("未找到广东大区选项")
            return False

        # 4. 点击湖南省的复选框
        # 先找到湖南省文本，然后找到同级的复选框
        hunan_text_xpath = '//li[contains(@id,"cascader-menu-") and contains(@id,"-1-2")]/span[1]/span[1]'
        hunan_text_element = tab.ele(f'xpath:{hunan_text_xpath}', timeout=3)

        if hunan_text_element:
            logger.info("找到湖南省文本")
            # 找到湖南省所在的li元素，然后找复选框
            hunan_li = '//li[contains(@id,"cascader-menu-") and contains(@id,"-1-2")]/label[1]/span[1]/span[1]'
            hunan_checkbox = tab.eles(f'xpath:{hunan_li}', timeout=3)

            for x in hunan_checkbox:
                logger.info(f"湖南省文本: {x.states.is_clickable}")
                if x.states.is_clickable:
                    hunan_checkbox = x
                    break

            if hunan_checkbox:
                hunan_checkbox.click()
                logger.info("成功点击湖南省复选框")
                time.sleep(2)

                # 关闭下拉菜单
                cascader_input.click()
                time.sleep(2)

                # 验证选择结果
                if tags_container:
                    new_hunan_tag = tags_container.ele('xpath:.//span[contains(text(), "湖南省")]', timeout=2)
                    if new_hunan_tag:
                        logger.info("✓ 成功添加湖南省标签")
                        return True
                    else:
                        logger.error("✗ 湖南省标签添加失败")
                        return False
            else:
                logger.error("未找到湖南省的复选框")
                return False
        else:
            logger.error("未找到湖南省选项")
            return False

    except Exception as e:
        logger.error(f"选择湖南省时出错: {e}")
        return False


# 日期选择
def select_time_province(tab, data_time):
    try:
        time_input = tab.ele('xpath://form[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[1]/div[1]/input[1]')
        if time_input:
            time_input.click()
            time.sleep(2)
            time_input_day = tab.eles('xpath://span[text()="按日"]', timeout=3)
            for x in time_input_day:
                logger.info(f'日期: {x.states.is_clickable}')
                if x.states.is_clickable:
                    time_input_day = x
                    break
            if time_input_day:
                time_input_day.click()
                logger.info('选择按日统计日期成功！')
            else:
                logger.error('没找到按日统计按钮！')
                return False

        day_input = tab.ele('xpath://form[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[2]/div[1]/input[1]')
        if day_input:
            day_input.click()
            # data_time = '2025 年 5 月 12 日'
            day_input_text = data_time[0: 11]  # 获取 "2025 年 5 月"
            target_day = data_time.split(' ')[-2]  # 获取日期部分 "12"

            # 处理前导零问题：同时准备带前导零和不带前导零的版本
            target_day_with_zero = target_day  # 原始格式（可能有前导零）
            target_day_no_zero = str(int(target_day))  # 去掉前导零的格式

            logger.info(f'判断当前月份是否为 {day_input_text}，目标日期: {target_day}（也尝试: {target_day_no_zero}）')

            # 循环查找并导航到目标月份
            for i in range(10):  # 增加循环次数以防万一
                time.sleep(2)
                # 获取当前显示的月份
                current_month_ele = tab.ele(
                    'xpath://div[contains(@class, "el-picker-panel__content el-date-range-picker__content is-left")]//div[contains(text(), "年")]')

                if current_month_ele:
                    current_month_text = current_month_ele.text
                    logger.info(f'当前显示月份: {current_month_text}')

                    # 比较当前月份与目标月份
                    if current_month_text == day_input_text:
                        logger.info('找到目标月份，开始选择日期')
                        break
                    else:
                        # 提取年份和月份数字进行比较
                        try:
                            current_parts = current_month_text.split(' ')
                            target_parts = day_input_text.split(' ')

                            current_year = int(current_parts[0])
                            current_month_num = int(current_parts[2].replace('月', ''))
                            target_year = int(target_parts[0])
                            target_month_num = int(target_parts[2].replace('月', ''))

                            logger.info(
                                f'当前: {current_year}年{current_month_num}月, 目标: {target_year}年{target_month_num}月')

                            # 比较年月组合
                            current_date_num = current_year * 12 + current_month_num
                            target_date_num = target_year * 12 + target_month_num

                            if target_date_num < current_date_num:
                                # 目标日期小于当前日期，点击左箭头
                                mon_left_but = tab.ele(
                                    'xpath://button[contains(@class, "el-picker-panel__icon-btn el-icon-arrow-left")]')
                                if mon_left_but:
                                    logger.info('点击左箭头，向前翻页')
                                    mon_left_but.click()
                                else:
                                    logger.error('找不到左箭头按钮')
                                    return False
                            elif target_date_num > current_date_num:
                                # 目标日期大于当前日期，点击右箭头
                                mon_right_but = tab.ele(
                                    'xpath://button[contains(@class, "el-picker-panel__icon-btn el-icon-arrow-right")]')
                                if mon_right_but:
                                    logger.info('点击右箭头，向后翻页')
                                    mon_right_but.click()
                                else:
                                    logger.error('找不到右箭头按钮')
                                    return False
                            else:
                                # 年月相等，说明已经找到了目标月份
                                logger.info('年月相等，找到目标月份')
                                break
                        except (ValueError, IndexError) as e:
                            logger.error(f'解析年月时出错: {e}')
                            logger.error(f'当前月份文本: {current_month_text}')
                            logger.error(f'目标月份文本: {day_input_text}')
                            return False
                else:
                    logger.error('找不到当前月份显示元素')
                    return False
            else:
                logger.error('超出查找月份次数！！！')
                return False

            # 选择具体的日期 - 防止部分匹配问题
            # 先找到所有包含目标数字的元素，然后筛选出精确匹配的
            day_element = None

            def find_exact_day_element(target_day_str):
                """查找精确匹配的日期元素"""
                logger.info(f'查找精确匹配的日期: {target_day_str}')

                # 先尝试精确匹配
                exact_element = tab.ele(
                    f'xpath://div[contains(@class, "el-picker-panel__content el-date-range-picker__content is-left")]//td[@class="available"]//span[normalize-space(text())="{target_day_str}"]')

                if exact_element:
                    logger.info(f'通过精确匹配找到日期: {target_day_str}')
                    return exact_element

                # 如果精确匹配失败，找到所有包含该数字的元素
                logger.info(f'精确匹配失败，查找所有包含 {target_day_str} 的元素')
                all_matching_elements = tab.eles(
                    f'xpath://div[contains(@class, "el-picker-panel__content el-date-range-picker__content is-left")]//td[@class="available"]//span[contains(text(), "{target_day_str}")]')

                if all_matching_elements:
                    logger.info(f'找到 {len(all_matching_elements)} 个包含 {target_day_str} 的元素')

                    # 遍历所有匹配的元素，找到精确匹配的
                    for element in all_matching_elements:
                        element_text = element.text.strip()
                        logger.info(f'检查元素文本: "{element_text}"')

                        # 精确匹配检查
                        if element_text == target_day_str:
                            logger.info(f'找到精确匹配的元素: {element_text}')
                            return element

                    logger.warning(f'没有找到精确匹配 {target_day_str} 的元素')
                    # 列出所有找到的文本用于调试
                    found_texts = [elem.text.strip() for elem in all_matching_elements]
                    logger.info(f'找到的文本: {found_texts}')
                else:
                    logger.warning(f'没有找到任何包含 {target_day_str} 的元素')

                return None

            # 方法1：尝试原始格式（带前导零）
            if target_day_with_zero:
                day_element = find_exact_day_element(target_day_with_zero)

            # 方法2：如果没找到，尝试不带前导零的版本
            if not day_element and target_day_no_zero != target_day_with_zero:
                day_element = find_exact_day_element(target_day_no_zero)

            if day_element:
                found_day = target_day_with_zero if day_element else target_day_no_zero
                logger.info(f'找到可用日期 {found_day}，进行双击')
                try:
                    # 等待元素可见和可点击
                    time.sleep(2)  # 等待页面稳定

                    # 检查元素是否可见
                    if day_element.states.is_displayed:
                        logger.info('元素可见，开始点击')
                        day_element.click()
                        time.sleep(1)  # 短暂等待
                        day_element.click()  # 双击
                        logger.info('日期选择完成')
                        return True
                    else:
                        logger.warning('元素不可见，尝试点击父元素td')
                        # 尝试点击td元素而不是span
                        td_element = day_element.parent()
                        if td_element:
                            td_element.click()
                            time.sleep(1)
                            td_element.click()
                            logger.info('通过点击td完成日期选择')
                            return True
                        else:
                            logger.error('找不到父元素td')
                            return False
                except Exception as e:
                    logger.error(f'选择日期时出错: {e}')
                    # 尝试使用DrissionPage的t:span@@tx()语法，同时尝试两种格式
                    try:
                        logger.info('尝试使用DrissionPage语法重新查找')

                        def find_exact_day_element_drission(target_day_str):
                            """使用DrissionPage语法查找精确匹配的日期元素"""
                            logger.info(f'使用DrissionPage语法查找: {target_day_str}')

                            # 先尝试精确匹配
                            exact_element = tab.ele(f't:span@@tx()={target_day_str}')
                            if exact_element:
                                logger.info(f'DrissionPage精确匹配找到: {target_day_str}')
                                return exact_element

                            # 如果精确匹配失败，找到所有span元素，手动筛选
                            logger.info(f'DrissionPage精确匹配失败，查找所有span元素')
                            all_spans = tab.eles('t:span')

                            if all_spans:
                                logger.info(f'找到 {len(all_spans)} 个span元素，开始筛选')
                                for span in all_spans:
                                    try:
                                        span_text = span.text.strip()
                                        if span_text == target_day_str:
                                            # 检查这个span是否在日期选择器的可用单元格中
                                            parent_td = span.parent()
                                            if parent_td and 'available' in parent_td.attr('class', ''):
                                                logger.info(f'找到精确匹配的可用日期span: {span_text}')
                                                return span
                                    except:
                                        continue

                            logger.warning(f'DrissionPage语法也没找到精确匹配的 {target_day_str}')
                            return None

                        day_element_alt = None

                        # 先尝试带前导零的
                        day_element_alt = find_exact_day_element_drission(target_day_with_zero)
                        if not day_element_alt:
                            # 再尝试不带前导零的
                            day_element_alt = find_exact_day_element_drission(target_day_no_zero)

                        if day_element_alt:
                            used_format = target_day_with_zero if day_element_alt else target_day_no_zero
                            logger.info(f'通过DrissionPage语法找到精确匹配的日期 {used_format}')
                            time.sleep(2)
                            day_element_alt.click()
                            time.sleep(1)
                            day_element_alt.click()
                            logger.info('日期选择完成')
                            return True
                        else:
                            logger.error(
                                f'DrissionPage语法也找不到精确匹配的日期 {target_day_with_zero} 或 {target_day_no_zero}')
                            # 调试：列出所有可用日期
                            available_days = tab.eles(
                                'xpath://div[contains(@class, "el-picker-panel__content el-date-range-picker__content is-left")]//td[@class="available"]//span')
                            if available_days:
                                available_dates = [day.text.strip() for day in available_days]
                                logger.info(f'当前月份可用日期: {available_dates}')
                            return False
                    except Exception as e2:
                        logger.error(f'使用DrissionPage语法时也出错: {e2}')
                        return False
            else:
                logger.error(f'找不到可用日期 {target_day_with_zero} 或 {target_day_no_zero}')
                # 调试：列出所有可用日期
                available_days = tab.eles(
                    'xpath://div[contains(@class, "el-picker-panel__content el-date-range-picker__content is-left")]//td[@class="available"]//span')
                if available_days:
                    available_dates = [day.text.strip() for day in available_days]
                    logger.info(f'当前月份可用日期: {available_dates}')
                return False

        else:
            logger.error('没找到日期input！')
            return False

    except Exception as e:
        logger.error(f"选择日期时出错: {e}")
        return False


# 获取数据并立即入库
def query_data(tab):
    # 获取当前日期
    today = datetime.date.today()

    # 获取昨天日期
    yesterday = today - datetime.timedelta(days=1)

    now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
    logger.info(f"查询日期: {now_today}")

    # 生成日期字段
    p_day_id = yesterday.strftime('%Y%m%d')

    try:
        # 语音人工呼入量（artCallinCt)
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-artCallinCt-0 TxtOver f_td_over_w")]')
        if element:
            artCallinCt = element.text.strip()
            logger.info(f"获取到 语音人工呼入量 值: {artCallinCt}")
            insert_indicator_data(p_day_id, 'artCallinCt', artCallinCt)
        else:
            logger.warning("未找到 语音人工呼入量 元素")

        # 10000/10001话务总量（用于计算语音自助话务占比）
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-connCt-0 TxtOver f_td_over_w")]')
        if element:
            connCt = element.text.strip()
            logger.info(f"获取到 10000/10001话务总量 值: {connCt}")

            # 计算语音自助话务占比
            if artCallinCt:
                try:
                    seifservicerate = (float(connCt) - float(artCallinCt)) / float(connCt) * 100
                    seifservicerate_formatted = f"{seifservicerate:.2f}"
                    logger.info(f"计算到 语音自助话务占比 值: {seifservicerate_formatted}")
                    insert_indicator_data(p_day_id, 'seifservicerate', seifservicerate_formatted)
                except (ValueError, ZeroDivisionError) as e:
                    logger.error(f"计算语音自助话务占比时出错: {e}")
            else:
                logger.warning("由于语音人工呼入量未获取，无法计算语音自助话务占比")
        else:
            logger.warning("未找到 10000/10001话务总量 元素")

        # 语音客服15s接通率（conn15Rate)
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-conn15Rate-0 TxtOver f_td_over_w")]')
        if element:
            conn15Rate = element.text.strip()
            logger.info(f"获取到 语音客服15s接通率 值: {conn15Rate}")
            insert_indicator_data(p_day_id, 'conn15Rate', conn15Rate)
        else:
            logger.warning("未找到 语音客服15s接通率 元素")

        # 10000号人工一解率（onceRate)
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-onceRate-0 TxtOver f_td_over_w")]')
        if element:
            onceRate = element.text.strip()
            logger.info(f"获取到 10000号人工一解率 值: {onceRate}")
            insert_indicator_data(p_day_id, 'onceRate', onceRate)
        else:
            logger.warning("未找到 10000号人工一解率 元素")

        # 10000号整体呼入量（artconn)
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-connCt-0 TxtOver f_td_over_w")]')
        if element:
            artconn = element.text.strip()
            logger.info(f"获取到 10000号整体呼入量 值: {artconn}")
            insert_indicator_data(p_day_id, 'artconn', artconn)
        else:
            logger.warning("未找到 10000号整体呼入量 元素")

        # 平台呼入10000自助量（wanselfcnt)
        element = tab.ele(
            'xpath://span[contains(@class, "el-tooltip item colbeyond-auto10000CallinCt-0 TxtOver f_td_over_w")]')
        if element:
            wanselfcnt = element.text.strip()
            logger.info(f"获取到 平台呼入10000自助量 值: {wanselfcnt}")
            insert_indicator_data(p_day_id, 'wanselfcnt', wanselfcnt)

            # 计算万号总量（wanvolumecnt）
            if artCallinCt:
                try:
                    wanvolumecnt = int(wanselfcnt) + int(artCallinCt)
                    logger.info(f"计算到 万号总量 值: {wanvolumecnt}")
                    insert_indicator_data(p_day_id, 'wanvolumecnt', str(wanvolumecnt))
                except (ValueError, TypeError) as e:
                    logger.error(f"计算万号总量时出错: {e}")
            else:
                logger.warning("由于语音人工呼入量未获取，无法计算万号总量")
        else:
            logger.warning("未找到 平台呼入10000自助量 元素")

        logger.info("所有数据获取和入库操作完成")

    except Exception as e:
        logger.error(f"获取数据时出错: {e}")


def query_zun_old(tab):
    # 获取昨天日期
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    p_day_id = yesterday.strftime('%Y%m%d')

    try:
        dl_input = tab.ele('xpath://form[1]/div[1]/div[5]/div[1]/div[1]/div[1]/div[1]/div[1]/input[1]')
        if dl_input:
            dl_input.click()
            time.sleep(2)
            dl_input.input('尊老')
            time.sleep(3)
            tab.ele('xpath://form/div[1]/div[5]/div/div/div/div/div[3]/div[1]/div[1]/ul/li[10]/span').click()
            time.sleep(3)
            tab.ele('xpath://button[@id="searchColClass-search"]', timeout=3).click()
            time.sleep(5)

            # 10000号适老化接通率（artConnRt）
            element = tab.ele(
                'xpath://span[contains(@class, "el-tooltip item colbeyond-artConnRt-0 TxtOver f_td_over_w")]')
            if element:
                artConnRt = element.text.strip()
                logger.info(f"获取到 10000号适老化接通率 值: {artConnRt}")
                insert_indicator_data(p_day_id, 'artConnRt', artConnRt)
            else:
                logger.warning("未找到 10000号适老化接通率 元素")

            logger.info("尊老数据获取和入库操作完成")

        else:
            logger.error('技能队列input获取失败！')

    except Exception as e:
        logger.error(f"尊老数据获取异常: {e}")


def query_cf_data(browser):
    # 获取昨天日期
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    p_day_id = yesterday.strftime('%Y%m%d')

    # 获取条件标签页
    try:
        tab = browser.get_tab(title='高频呼入统计报表')
        if tab is None:
            logger.warning("未找到 高频呼入统计报表 标签页，跳过该部分")
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
                insert_indicator_data(p_day_id, 'repeatRate', repeatRate)
            else:
                logger.warning("未找到 10000号重复来电率 元素")

            logger.info("重复来电率数据获取和入库操作完成")

        except Exception as e:
            logger.error(f"10000号重复来电率数据获取出错: {e}")

        finally:
            tab.close()
