import time

from DrissionPage import Chromium

from util.captcha_utils import recognize_captcha, recognize_captcha_simple, refresh_captcha


def auto_login(tab, username, password, max_retry=5, use_simple_ocr=True):
    """
    自动登录函数

    Args:
        tab: DrissionPage的tab对象
        username: 用户名
        password: 密码
        max_retry: 最大重试次数
        use_simple_ocr: 是否使用简化版OCR识别
    """

    for attempt in range(max_retry):
        try:
            print(f"登录尝试 {attempt + 1}/{max_retry}")

            # 等待页面加载完成
            time.sleep(2)

            # 清空并输入用户名
            username_input = tab.ele('#userName', timeout=10)
            if username_input:
                username_input.clear()
                username_input.input(username)
                print(f"已输入用户名: {username}")
            else:
                print("未找到用户名输入框")
                continue

            # 清空并输入密码
            password_input = tab.ele('#userPwd', timeout=5)
            if password_input:
                password_input.clear()
                password_input.input(password)
                print("已输入密码")
            else:
                print("未找到密码输入框")
                continue

            # 如果不是第一次尝试，先刷新验证码
            if attempt > 0:
                refresh_captcha(tab)

            # 识别并输入验证码
            if use_simple_ocr:
                captcha_text = recognize_captcha_simple(tab)
            else:
                captcha_text = recognize_captcha(tab)

            if captcha_text and len(captcha_text) >= 3:  # 验证码通常是4位，至少要3位才尝试
                captcha_input = tab.ele('#loginCaptcha', timeout=5)
                if captcha_input:
                    captcha_input.clear()
                    captcha_input.input(captcha_text)
                    print(f"已输入验证码: {captcha_text}")
                else:
                    print("未找到验证码输入框")
                    continue

                # 点击登录按钮
                tab.run_js('login()')
                print("已点击登录按钮")

                # 等待登录结果
                time.sleep(3)

                # 检查是否登录成功
                current_url = tab.url
                print(f"当前URL: {current_url}")

                # 判断登录是否成功的条件（可根据实际情况调整）
                if '/LJYY/loginCtrl/login.do' not in current_url:
                    print("登录成功！")
                    return True

                # 检查页面中是否有成功标识
                page_html = tab.html
                if '登录成功' in page_html or '欢迎' in page_html or 'welcome' in page_html.lower():
                    print("登录成功！")
                    return True

                # 检查错误消息
                error_msg = tab.ele('#msg', timeout=2)
                if error_msg and error_msg.text.strip():
                    error_text = error_msg.text.strip()
                    print(f"登录失败: {error_text}")
                    if '验证码' in error_text or 'captcha' in error_text.lower():
                        print("验证码错误，重试...")
                        continue
                    elif '用户名' in error_text or '密码' in error_text:
                        print("用户名或密码错误")
                        return False
                    else:
                        print("其他登录错误，重试...")
                        continue
                else:
                    print("未获取到明确的错误信息，可能验证码错误，重试...")
                    continue

            else:
                print("验证码识别失败或长度不足，重试...")
                refresh_captcha(tab)
                continue

        except Exception as e:
            print(f"登录过程中出错: {e}")
            continue

    print(f"登录失败，已重试 {max_retry} 次")
    return False


def handle_ssl_warning(tab):
    """
    处理SSL证书警告页面
    """
    try:
        time.sleep(2)
        ssl_warning_title = tab.ele('tag:h1@@text():您的连接不是私密连接', timeout=3)

        if ssl_warning_title:
            print("检测到SSL证书警告页面")
            advanced_button = tab.ele('#details-button', timeout=3)

            if advanced_button:
                print("找到高级按钮，正在点击...")
                advanced_button.click()
                time.sleep(1)

                proceed_link = tab.ele('#proceed-link', timeout=3)
                if proceed_link:
                    print("找到继续前往链接，正在点击...")
                    proceed_link.click()
                    print("已点击继续前往，正在跳过SSL警告...")
                    time.sleep(3)
                    return True
                else:
                    print("未找到继续前往链接")
                    return False
            else:
                print("未找到高级按钮")
                return False
        else:
            print("未检测到SSL警告页面，继续正常流程")
            return True

    except Exception as e:
        print(f"处理SSL警告时出错: {e}")
        return False


if __name__ == "__main__":
    # 配置登录信息
    USERNAME = "luocl"  # 请替换为实际用户名
    PASSWORD = "Admin350370#"  # 请替换为实际密码

    try:
        # 创建浏览器实例
        tab = Chromium().latest_tab

        # 访问登录页面
        tab.get("https://10.141.136.171:10304/LJYY/")

        # 处理SSL警告（如果需要）
        if handle_ssl_warning(tab):
            # 执行自动登录
            # use_simple_ocr=True 使用简化版OCR，通常效果更好
            # use_simple_ocr=False 使用带预处理的OCR
            if auto_login(tab, USERNAME, PASSWORD, max_retry=5, use_simple_ocr=True):
                print("自动登录完成！")

                # 登录成功后的操作
                print("可以继续执行后续操作...")

            else:
                print("自动登录失败！")
        else:
            print("SSL警告处理失败")

    except Exception as e:
        print(f"主程序执行出错: {e}")
