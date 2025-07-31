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
