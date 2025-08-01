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

logger.info("浏览器配置完成，启动浏览器...")
try:
    browser_instance = Chromium(addr_or_opts=chrome_options, session_options=False)
    browser = browser_instance.latest_tab
    logger.info("浏览器启动成功")
except Exception as e:
    logger.error(f"浏览器启动失败: {e}")
    raise

logger.info("访问10000号运营管理平台...")
try:
    browser.get('https://132.126.196.99:20019/unifiedLogin?clientId=CTPLAT')
    time.sleep(5)
    logger.info("网站访问成功")
except Exception as e:
    logger.error(f"网站访问失败: {e}")
    raise

# 输入账号
logger.info("开始输入登录凭据...")
try:
    user_name = browser.ele('xpath://*[@id="pane-first"]/div/form/div[1]/div/div/input', timeout=5)
    user_name.input('17375743687', clear=True)
    time.sleep(2)

    # 输入密码
    user_password = browser.ele('xpath://*[@id="pane-first"]/div/form/div[2]/div/div/input', timeout=5)
    user_password.input('Zy.7140816677', clear=True)
    time.sleep(2)
    logger.info("登录凭据输入成功")
except Exception as e:
    logger.error(f"登录凭据输入失败: {e}")
    raise

# 点击同意书
logger.info("勾选用户协议...")
try:
    browser.ele('xpath://*[@id="checkBeforeLogin"]/span[1]/span').click()
    time.sleep(2)
    logger.info("用户协议勾选成功")
except Exception as e:
    logger.error(f"用户协议勾选失败: {e}")
    raise

logger.info("点击登录按钮...")
try:
    browser.ele('xpath://*[@id="pane-first"]/div/form/div[4]/div/button').click()
    time.sleep(2)
    logger.info("登录按钮点击成功")
except Exception as e:
    logger.error(f"登录按钮点击失败: {e}")
    raise

# 滑动验证
logger.info("处理滑动验证码...")
try:
    handle_image(browser)
    logger.info("滑动验证码处理成功")
except Exception as e:
    logger.error(f"滑动验证码处理失败: {e}")
    raise

# 短信验证
logger.info("获取短信验证码...")
try:
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
    logger.info("短信验证码处理成功")
except Exception as e:
    logger.error(f"短信验证码处理失败: {e}")
    raise

# 打开 话务运营重点指标
logger.info("登录成功，导航到话务运营重点指标...")
try:
    browser.ele('xpath://*[@id="main"]/div[3]/section/section/aside/div/div/ul/li[1]').click()
    time.sleep(2)
    browser.ele('xpath://ul/li[1]/span[text()="话务运营重点指标"]').click()
    time.sleep(2)
    browser.ele('xpath://ul/li[2]/span[text()="高频呼入统计报表"]').click()
    time.sleep(2)
    logger.info("导航到话务运营重点指标成功")
except Exception as e:
    logger.error(f"导航到话务运营重点指标失败: {e}")
    raise

logger.info("选择湖南省...")
try:
    select_hunan_province(browser)
    logger.info("湖南省选择成功")
except Exception as e:
    logger.error(f"湖南省选择失败: {e}")
    raise

# 获取当前日期
logger.info("设置查询时间为昨天...")
try:
    today = dt.date.today()
    # 获取昨天日期
    yesterday = today - dt.timedelta(days=1)
    now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
    select_time_province(browser, now_today)
    browser.ele('xpath://button[@id="searchColClass-search"]/span[1]').click()
    time.sleep(5)
    logger.info("查询时间设置成功")
except Exception as e:
    logger.error(f"查询时间设置失败: {e}")
    raise

logger.info("开始查询数据...")
try:
    query_data(browser)
    logger.info("基础数据查询成功")
except Exception as e:
    logger.error(f"基础数据查询失败: {e}")
    raise

try:
    query_zun_old(browser)
    logger.info("尊老数据查询成功")
except Exception as e:
    logger.error(f"尊老数据查询失败: {e}")
    raise

# 高频呼入统计包报表
logger.info("查询高频呼入统计报表...")
try:
    query_cf_data(browser_instance)
    logger.info("高频呼入统计报表查询成功")
except Exception as e:
    logger.error(f"高频呼入统计报表查询失败: {e}")
    raise

logger.info("程序执行完成，关闭浏览器...")
try:
    browser.close()
    logger.info("浏览器关闭成功")
except Exception as e:
    logger.error(f"浏览器关闭失败: {e}")

time.sleep(20)
