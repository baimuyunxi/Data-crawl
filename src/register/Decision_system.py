import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from src.AuthCode.mesmain import Email189VerificationTool
from src.decisionSys.order_monitor import get_order_duplicate, get_order_kd, get_order_kd_online, get_order_kd_pre, \
    get_strictest_work_oder, get_order_wh_been, get_order_yd


def main():
    print("开始登录客分决策系统！")

    chrome_options = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

    # 创建ChromiumOptions实例并配置启动参数
    # chrome_options.set_argument('--ssl-version-min=tls1')
    # chrome_options.set_argument('--ssl-version-max=tls1.2')
    chrome_options.set_argument('--ignore-certificate-errors')
    chrome_options.set_argument('--ignore-ssl-errors')

    try:
        browser_instance = Chromium(addr_or_opts=chrome_options, session_options=False)
        browser = browser_instance.latest_tab
    except Exception as e:
        raise

    print("访问目标网站...")
    browser.get(
        'https://web.oauth.tyrzzx.eda.it.hnx.ctc.com:15099/index.html?client_id=TYRZ_JCZC&client_secret=TYRZ_JCZC&redirect_uri=https://134.176.82.81:30050/rating/static/index.html#/signOnUac')
    time.sleep(5)

    # 输入账号
    user_name = browser.ele('xpath://*[@id="phoneInputDouble"]', timeout=5)
    user_name.input('17375743687')
    time.sleep(2)

    # 输入密码
    user_password = browser.ele('xpath://*[@id="pwdInputDouble"]', timeout=5)
    user_password.input('Zy.714!0861')
    time.sleep(2)

    # 短信
    browser.ele('xpath://*[@id="codeBtnTextDouble"]', timeout=5).click()
    mail_time = datetime.now()
    email_tool = Email189VerificationTool()
    result = email_tool.get_verification_code("统一认证中心", mail_time)
    email_code = browser.ele('xpath://*[@id="msgInputDouble"]')
    email_code.input(result)
    time.sleep(2)
    browser.ele('xpath://*[@id="loginBtn"]').click()
    time.sleep(20)
    browser.ele(
        'xpath://*[@id="root"]/div/section/section/main/div/div[3]/div/div[2]/div/span/span/span/button').click()

    get_strictest_work_oder()
    get_order_duplicate()
    get_order_wh_been()
    get_order_yd()  ##
    get_order_kd()  ##
    get_order_kd_online()
    get_order_kd_pre()

    browser.close()


if __name__ == "__main__":
    main()
