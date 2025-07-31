import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from src.AuthCode.mesmain import Email189VerificationTool
from src.region.importtation import IM_porttation_main
from src.util.verificationCode.ImageCode import recognize_captcha_simple

print("开始登录 IM客户运营支撑平台 ！")

co = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

browser = Chromium(addr_or_opts=co, session_options=False).latest_tab

browser.get("http://10.135.4.28/IMAdmin/system/login!loginOut.action")
time.sleep(5)

# 输入账号
user_name = browser.ele('xpath://*[@id="loginName"]', timeout=5)
user_name.input('46278')
time.sleep(2)

# 输入密码
user_password = browser.ele('xpath://*[@id="pwd"]', timeout=5)
user_password.input('zzz159159.')
time.sleep(2)

# 验证码模块
captcha_img = recognize_captcha_simple(browser, 'xpath://*[@id="loginCodeImage"]')
auth_code = browser.ele('xpath://*[@id="loginCodeRand"]', timeout=5)
auth_code.input(captcha_img)
time.sleep(2)

# 登录
browser.ele('xpath://html/body/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[3]/td[3]/input',
            timeout=5).click()
time.sleep(2)

# 验证码
browser.ele('xpath://*[@id="verify_code"]', timeout=5).click()
mail_time = datetime.now()
email_tool = Email189VerificationTool()
result = email_tool.get_verification_code("IM运营平台", mail_time)
email_code = browser.ele('xpath://*[@id="loginName"]')
print(f"获取到 短信验证码 为: {result}")
email_code.input(result)
time.sleep(1)
browser.ele('xpath://*[@id="login_in"]').click()
time.sleep(10)

# 页面操作
browser.ele('xpath://*[@id="btn"]', timeout=5).click()
time.sleep(5)
browser.ele('xpath://*[@id="firstMenuItem_148"]', timeout=5).click()
time.sleep(8)

# 打开 IM会话服务报表
browser.ele('xpath://*[@id="dcmsTree_1481"]/div[1]/a[2]', timeout=5).click()
time.sleep(2)
browser.ele('xpath://*[@id="dcmsTree_1482"]/div[1]/a[2]', timeout=5).click()
time.sleep(2)
browser.ele('xpath://*[@id="scmsTree_14894"]', timeout=5).click()
time.sleep(2)

# 打开 远程柜台会话服务报表
browser.ele('xpath://*[@id="dcmsTree_1482"]/div[9]/a[2]', timeout=5).click()
time.sleep(2)
browser.ele('xpath://*[@id="scmsTree_148118"]', timeout=5).click()
time.sleep(2)

IM_porttation_main()

# 关闭浏览器
browser.close()
