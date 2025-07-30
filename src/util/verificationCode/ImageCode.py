import re
import time
from io import BytesIO

from PIL import Image

import ddddocr


def preprocess_captcha_image(image):
    """
    预处理验证码图片以提高OCR识别率
    """
    # 转换为灰度图
    gray = image.convert('L')

    # 增强对比度
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2.0)

    # 二值化处理
    threshold = 128
    binary = enhanced.point(lambda x: 0 if x < threshold else 255, '1')

    return binary


def recognize_captcha(tab, captcha_img_selector='#img'):
    """
    使用ddddocr识别验证码
    """
    try:
        # 获取验证码图片元素
        captcha_img = tab.ele(captcha_img_selector, timeout=5)
        if not captcha_img:
            print("未找到验证码图片元素")
            return None

        # 截取验证码图片
        img_data = captcha_img.get_screenshot()

        if img_data:
            # 创建ddddocr识别器
            ocr = ddddocr.DdddOcr(show_ad=False)  # show_ad=False关闭广告

            # 直接使用原始图片进行识别
            captcha_text = ocr.classification(img_data)

            # 如果直接识别效果不好，可以尝试预处理后再识别
            if not captcha_text or len(captcha_text) < 3:
                print("直接识别效果不佳，尝试预处理图片...")
                # 将截图数据转换为PIL Image对象
                image = Image.open(BytesIO(img_data))

                # 预处理图片
                processed_image = preprocess_captcha_image(image)

                # 保存处理后的图片用于调试
                processed_image.save('captcha_debug.png')

                # 将处理后的图片转换为字节数据
                img_buffer = BytesIO()
                processed_image.save(img_buffer, format='PNG')
                processed_img_data = img_buffer.getvalue()

                # 使用处理后的图片进行识别
                captcha_text = ocr.classification(processed_img_data)

            # 清理识别结果，只保留数字和字母
            captcha_text = re.sub(r'[^0-9A-Za-z]', '', captcha_text)

            print(f"识别到验证码: {captcha_text}")
            return captcha_text
        else:
            print("无法获取验证码图片数据")
            return None

    except Exception as e:
        print(f"验证码识别失败: {e}")
        return None


def recognize_captcha_simple(tab, captcha_img_selector='#img'):
    """
    简化版验证码识别，直接使用ddddocr，不进行预处理
    """
    try:
        # 获取验证码图片元素
        captcha_img = tab.ele(captcha_img_selector, timeout=5)
        if not captcha_img:
            print("未找到验证码图片元素")
            return None

        # 截取验证码图片
        img_data = captcha_img.get_screenshot()

        if img_data:
            # 创建ddddocr识别器
            ocr = ddddocr.DdddOcr(show_ad=False)

            # 直接识别
            captcha_text = ocr.classification(img_data)

            # 清理识别结果
            captcha_text = re.sub(r'[^0-9A-Za-z]', '', captcha_text)

            print(f"识别到验证码: {captcha_text}")
            return captcha_text
        else:
            print("无法获取验证码图片数据")
            return None

    except Exception as e:
        print(f"验证码识别失败: {e}")
        return None


def refresh_captcha(tab, captcha_img_selector='#img'):
    """
    刷新验证码
    """
    try:
        captcha_img = tab.ele(captcha_img_selector, timeout=5)
        if captcha_img:
            captcha_img.click()
            time.sleep(2)  # 等待验证码加载
            print("验证码已刷新")
            return True
    except Exception as e:
        print(f"刷新验证码失败: {e}")
    return False


def handle_slide_captcha(tab, max_wait_time=30):
    """
    处理滑动验证码

    Args:
        tab: DrissionPage的tab对象
        max_wait_time: 最大等待时间（秒）

    Returns:
        bool: 验证是否成功
    """
    try:
        print("检查是否出现滑动验证码...")

        # 等待验证对话框出现
        verify_dialog = tab.ele('.verifyDialog', timeout=5)
        if not verify_dialog:
            print("未检测到滑动验证码对话框")
            return True  # 没有验证码就认为成功

        # 检查对话框是否显示
        dialog_style = verify_dialog.attr('style')
        if 'display: none' in dialog_style:
            print("验证码对话框未显示")
            return True

        print("检测到滑动验证码，开始处理...")

        # 等待验证码加载完成
        time.sleep(3)

        # 查找滑动验证码相关元素
        # 这里需要根据实际的滑动验证码结构来调整选择器
        slider_track = tab.ele('.slider-track, .captcha-slider, .slide-verify', timeout=10)
        slider_button = tab.ele('.slider-button, .slide-btn, .slider-move-btn', timeout=10)

        if not slider_track or not slider_button:
            print("未找到滑动验证码元素，尝试查找其他可能的元素...")

            # 尝试其他可能的选择器
            slider_elements = [
                '.geetest_slider_button',
                '.yidun_slider',
                '.slider-btn',
                '.captcha-move-btn',
                '[class*="slider"]',
                '[class*="captcha"]'
            ]

            for selector in slider_elements:
                element = tab.ele(selector, timeout=2)
                if element:
                    slider_button = element
                    print(f"找到滑动按钮: {selector}")
                    break

        if slider_button:
            try:
                # 获取滑动按钮的位置和大小
                button_rect = slider_button.rect

                # 计算滑动距离（通常需要滑动到右侧）
                # 这里可能需要根据实际验证码调整滑动距离
                slide_distance = 200  # 默认滑动距离

                # 尝试获取滑动轨道来计算准确距离
                if slider_track:
                    track_rect = slider_track.rect
                    slide_distance = track_rect.width - button_rect.width - 10

                print(f"开始滑动验证码，滑动距离: {slide_distance}px")

                # 执行滑动操作
                # 方法1: 使用拖拽
                tab.actions.drag(slider_button, (slide_distance, 0), duration=1.5)

                # 等待验证结果
                time.sleep(2)

                # 检查验证是否成功
                # 方法1: 检查对话框是否消失
                dialog_style = verify_dialog.attr('style')
                if 'display: none' in dialog_style:
                    print("滑动验证码验证成功！")
                    return True

                # 方法2: 检查是否有成功标识
                success_elements = [
                    '.verify-success',
                    '.captcha-success',
                    '.slide-success',
                    '[class*="success"]'
                ]

                for selector in success_elements:
                    if tab.ele(selector, timeout=2):
                        print("滑动验证码验证成功！")
                        return True

                # 如果第一次滑动失败，尝试不同的滑动方式
                print("第一次滑动可能失败，尝试其他方式...")

                # 方法2: 使用模拟人工滑动（更自然的曲线滑动）
                start_x = button_rect.x + button_rect.width // 2
                start_y = button_rect.y + button_rect.height // 2

                # 分段滑动，模拟人工操作
                segments = 5
                segment_distance = slide_distance // segments

                for i in range(segments):
                    # 添加一些随机性来模拟人工操作
                    import random
                    offset_y = random.randint(-2, 2)
                    current_distance = segment_distance * (i + 1)

                    # 执行分段滑动
                    tab.actions.move_to((start_x + current_distance, start_y + offset_y))
                    time.sleep(random.uniform(0.1, 0.3))

                # 等待验证结果
                time.sleep(3)

                # 再次检查验证结果
                dialog_style = verify_dialog.attr('style')
                if 'display: none' in dialog_style:
                    print("滑动验证码验证成功！")
                    return True

                print("滑动验证码验证失败")
                return False

            except Exception as e:
                print(f"滑动操作失败: {e}")
                return False

        else:
            print("未找到可滑动的元素")
            return False

    except Exception as e:
        print(f"处理滑动验证码时出错: {e}")
        return False


def check_verification_dialog(tab):
    """
    检查验证对话框是否出现

    Args:
        tab: DrissionPage的tab对象

    Returns:
        bool: 是否出现验证对话框
    """
    try:
        verify_dialog = tab.ele('.verifyDialog', timeout=3)
        if verify_dialog:
            dialog_style = verify_dialog.attr('style')
            if 'display: none' not in dialog_style:
                return True
        return False
    except:
        return False
