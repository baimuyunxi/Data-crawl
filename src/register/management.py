import time

from DrissionPage import Chromium, ChromiumOptions

print("开始登录 10000号运营管理平台！")

chrome_options = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

chrome_options.set_argument('--ignore-certificate-errors')
chrome_options.set_argument('--ignore-ssl-errors')

browser_instance = Chromium(addr_or_opts=chrome_options, session_options=False)
browser = browser_instance.latest_tab

browser.get('https://132.126.196.99:20019/unifiedLogin?clientId=CTPLAT')
time.sleep(5)

# 输入账号
user_name = browser.ele('xpath://*[@id="pane-first"]/div/form/div[1]/div/div/input', timeout=5)
user_name.input('17375743687', clear=True)
time.sleep(2)

# 输入密码
user_password = browser.ele('xpath://*[@id="pane-first"]/div/form/div[2]/div/div/input', timeout=5)
user_password.input('Zy.7140816677', clear=True)
time.sleep(2)

# 点击同意书
browser.ele('xpath://*[@id="checkBeforeLogin"]/span[1]/span').click()
time.sleep(2)

browser.ele('xpath://*[@id="pane-first"]/div/form/div[4]/div/button').click()
time.sleep(2)
