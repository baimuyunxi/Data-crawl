import datetime as dt
import logging
import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from src.AuthCode.mesmain import Email189VerificationTool
from src.util.hw_util import query_data, query_zun_old, query_cf_data, select_hunan_province, select_time_province
from src.util.verificationCode.SlidingCode import handle_image

logger = logging.getLogger(__name__)

logger.info("开始登录 10000号运营管理平台！")

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

# 滑动验证
handle_image(browser)

# 短信验证
browser.ele('xpath://*[@id="main"]/div[3]/div[1]/div[3]/div[2]/form/div[2]/div/a').click()
mail_time = datetime.now()
email_tool = Email189VerificationTool()
result = email_tool.get_verification_code("10000号集约运管系统", mail_time)
email_code = browser.ele('xpath://*[@id="main"]/div[3]/div[1]/div[3]/div[2]/form/div[2]/div/div/input')
logger.info(f"获取到 短信验证码 为: {result}")
email_code.input(result)
time.sleep(1)
browser.ele('xpath://*[@id="main"]/div[3]/div[1]/div[3]/div[2]/form/div[3]/div/button').click()
time.sleep(20)

# 打开 话务运营重点指标
browser.ele('xpath://*[@id="main"]/div[3]/section/section/aside/div/div/ul/li[1]').click()
time.sleep(2)
browser.ele('xpath://ul/li[1]/span[text()="话务运营重点指标"]').click()
time.sleep(2)
browser.ele('xpath://ul/li[2]/span[text()="高频呼入统计报表"]').click()
time.sleep(2)

select_hunan_province(browser)

# 获取当前日期
today = dt.date.today()
# 获取昨天日期
yesterday = today - dt.timedelta(days=1)
now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
select_time_province(browser, now_today)
browser.ele('xpath://button[@id="searchColClass-search"]/span[1]').click()
time.sleep(5)

query_data(browser)
query_zun_old(browser)

# 高频呼入统计包报表
query_cf_data(browser_instance)

browser.close()
