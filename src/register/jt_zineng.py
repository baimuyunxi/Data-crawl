import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from src.AuthCode.mesmain import Email189VerificationTool
from src.intelligent.navigation import jt_4a_main
from src.util.verificationCode.ImageCode import recognize_captcha_simple

print("开始登录 集团4A平台 ！")

chrome_options = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

# 创建ChromiumOptions实例并配置启动参数
chrome_options.set_argument('--ssl-version-min=tls1')
chrome_options.set_argument('--ssl-version-max=tls1.2')
chrome_options.set_argument('--ignore-certificate-errors')
chrome_options.set_argument('--ignore-ssl-errors')

browser_instance = Chromium(addr_or_opts=chrome_options, session_options=False)
browser = browser_instance.latest_tab

# 访问您的目标网站
browser.get("https://sdpc.dianxin.com")
time.sleep(5)

# 登陆集团 4A 渠道
# 输入账号
user_name = browser.ele('xpath://*[@id="j_username"]', timeout=5)
user_name.input('17375743687')
time.sleep(2)

# 输入密码
user_password = browser.ele('xpath://*[@id="authen1Form"]/ul/li[2]/div', timeout=5)
user_password.input('Zyx.131471408661')
time.sleep(2)

browser.ele('xpath://*[@id="authen1Form"]/button').click()
time.sleep(2)

# 验证码模块
# 图片
captcha_img = recognize_captcha_simple(browser, 'xpath://*[@id="j_checkcodeImgCode24"]')
auth_code = browser.ele('xpath://*[@id="fs4_checkcode"]', timeout=5)
auth_code.input(captcha_img)
time.sleep(2)

# 短信
browser.ele('xpath://*[@id="smsBtn"]', timeout=5).click()
mail_time = datetime.now()
email_tool = Email189VerificationTool()
result = email_tool.get_verification_code("云认证", mail_time)
email_code = browser.ele('xpath://*[@id="sms_otpOrSms24"]')
print(f"获取到 短信验证码 为: {result}")
email_code.input(result)
time.sleep(1)
browser.ele('xpath://*[@id="authen4Form"]/button').click()
time.sleep(20)

# 代理加载
browser.refresh()
time.sleep(10)
browser.ele('xpath://html/body/div[2]/div/div[1]/button/i').click()
time.sleep(2)
browser.ele('xpath://*[@id="accordion"]/div[2]/ul/div[4]/li/span').click()
time.sleep(2)
browser.ele('xpath://*[@id="app"]/div/div[3]/div[3]/div/div/div[1]/div[4]/div/div[1]/div/div[1]/button/span').click()
time.sleep(15)

# 导航运管2.0平台 - 创建新标签页
tab_1 = browser_instance.new_tab()  # 先创建空标签页
tab_1.get('http://10.146.67.185:18090/znkf2.0/login.html')  # 然后导航到目标地址
time.sleep(3)

navigation_name = tab_1.ele('xpath://*[@id="txtName"]')
navigation_name.input('hun_zhuyinxi')
time.sleep(2)

navigation_password = tab_1.ele('xpath://*[@id="password"]')
navigation_password.input('Zyx714086')
time.sleep(2)

navigation_img = recognize_captcha_simple(tab_1, 'xpath://*[@id="imgValid"]')
navigation_code = tab_1.ele('xpath://*[@id="txtValid"]', timeout=5)
navigation_code.input(navigation_img)
time.sleep(2)

tab_1.ele('xpath://*[@id="sendCodeBtn"]', timeout=5).click()
mail_time = datetime.now()
email_tool = Email189VerificationTool()
result = email_tool.get_verification_code("电信小知", mail_time)
email_code = tab_1.ele('xpath://*[@id="smsCode"]', timeout=5)
print(f"获取到 短信验证码 为: {result}")
email_code.input(result)
time.sleep(1)
tab_1.ele('xpath://*[@id="cbox"]/div/div[2]/input').click()
time.sleep(3)

# 数字人运营管理平台 - 创建另一个新标签页
tab_2 = browser_instance.new_tab()  # 先创建空标签页
tab_2.get('http://10.143.168.41:8080/szzcplatformweb')  # 然后导航到目标地址
time.sleep(3)

digital_name = tab_2.ele('xpath://*[@id="app"]/div/div[2]/form/div[2]/div/div/input')
digital_name.input('17375743687')
time.sleep(2)

digital_password = tab_2.ele('xpath://*[@id="app"]/div/div[2]/form/div[3]/div/div/input')
digital_password.input('M2s5#6hL')
time.sleep(2)

digital_img = recognize_captcha_simple(tab_2, 'xpath://*[@id="app"]/div/div[2]/form/div[4]/div/div[2]/img')
digital_code = tab_2.ele('xpath://*[@id="app"]/div/div[2]/form/div[4]/div/div[1]/input', timeout=5)
digital_code.input(digital_img)
time.sleep(2)

tab_2.ele('xpath://*[@id="app"]/div/div[2]/form/div[5]/div/button').click()
time.sleep(2)

jt_4a_main()

browser.close()
