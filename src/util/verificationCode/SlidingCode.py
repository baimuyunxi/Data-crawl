import random
import time

from DrissionPage import Chromium, ChromiumOptions

from src.util.verificationCode.util.yunCode import verify


def get_random_distribution(total, count):
    """随机拆分总距离为n份"""
    if count == 1:
        return [total]

    item = total / count
    item = item + random.randint(int(-item * 2), int(item * 3))
    item = int(item)

    if item <= 0:
        item = 1
    if item >= total:
        item = total - 1

    return [item] + get_random_distribution(total - item, count - 1)


def get_steps(total, count):
    """获取每次滑动的累积X坐标"""
    distribution = get_random_distribution(total, count)
    steps = []
    cumulative = 0
    for item in distribution:
        cumulative += item
        steps.append(cumulative)
    return steps


def simulate_drag(browser, slider_element, distance):
    """模拟人工滑动轨迹"""
    count = 30  # 分成30步进行滑动
    total_duration = 8000  # 总耗时8秒(毫秒)

    # 获取滑块初始位置
    slider_rect = slider_element.rect
    start_x = slider_rect.midpoint[0]
    start_y = slider_rect.midpoint[1]

    # 获取每步的位移
    steps = get_steps(distance, count)

    # 开始拖拽
    browser.actions.hold(slider_element)

    for i, step in enumerate(steps):
        # 计算当前应该移动到的位置
        current_x = start_x + step
        current_y = start_y + random.randint(-5, 40)  # y轴随机偏移

        # 计算每步的持续时间(毫秒)
        step_duration = random.randint(
            int(total_duration / count / 2),
            int(total_duration / count * 2)
        )

        # 移动到目标位置
        browser.actions.move_to((current_x, current_y))

        # 等待随机时间
        time.sleep(step_duration / 1000.0)  # 转换为秒

    # 释放滑块
    browser.actions.release()


def handle_image(browser):
    """处理滑动验证码"""
    # 定位验证码元素
    captcha_element = browser.ele('xpath://*[@id="captcha"]/canvas[1]')

    # 截屏保存该元素
    captcha_element.get_screenshot(path='captcha_screenshot.png')

    # 识别验证码获取距离
    captcha_code = verify()

    # 定位滑动块元素
    slider_element = browser.ele('xpath://*[@id="captcha"]/div[2]/div/div')

    if slider_element:
        print(f"开始滑动验证码，距离: {captcha_code}像素")

        # 模拟滑动
        simulate_drag(browser, slider_element, int(captcha_code) + 12)

        print("滑动完成")

        # 等待验证结果
        time.sleep(2)

    else:
        print("未找到滑动块元素")


if __name__ == '__main__':
    chrome_options = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

    chrome_options.set_argument('--ignore-certificate-errors')
    chrome_options.set_argument('--ignore-ssl-errors')

    browser_instance = Chromium(addr_or_opts=chrome_options, session_options=False)
    browser = browser_instance.latest_tab

    handle_image(browser)
