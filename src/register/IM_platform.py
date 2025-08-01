import logging
import time
from datetime import datetime

from DrissionPage import Chromium, ChromiumOptions

from src.AuthCode.mesmain import Email189VerificationTool
from src.region.importtation import IM_porttation_main
from src.util.verificationCode.ImageCode import recognize_captcha_simple

logger = logging.getLogger(__name__)

logger.info("开始登录 IM客户运营支撑平台 ！")

co = (ChromiumOptions(read_file=False).set_browser_path(r'./Chrome/App/chrome.exe'))

logger.info("浏览器配置完成，启动浏览器...")
try:
    browser = Chromium(addr_or_opts=co, session_options=False).latest_tab
    logger.info("浏览器启动成功")
except Exception as e:
    logger.error(f"浏览器启动失败: {e}")
    raise

logger.info("访问IM客户运营支撑平台...")
try:
    browser.get("http://10.135.4.28/IMAdmin/system/login!loginOut.action")
    time.sleep(5)
    logger.info("网站访问成功")
except Exception as e:
    logger.error(f"网站访问失败: {e}")
    raise

# 输入账号
logger.info("开始输入登录凭据...")
try:
    user_name = browser.ele('xpath://*[@id="loginName"]', timeout=5)
    user_name.input('46278')
    time.sleep(2)

    # 输入密码
    user_password = browser.ele('xpath://*[@id="pwd"]', timeout=5)
    user_password.input('zzz159159.')
    time.sleep(2)
    logger.info("登录凭据输入成功")
except Exception as e:
    logger.error(f"登录凭据输入失败: {e}")
    raise

# 验证码模块
logger.info("处理图片验证码...")
try:
    captcha_img = recognize_captcha_simple(browser, 'xpath://*[@id="loginCodeImage"]')
    auth_code = browser.ele('xpath://*[@id="loginCodeRand"]', timeout=5)
    auth_code.input(captcha_img)
    time.sleep(2)
    logger.info("图片验证码处理成功")
except Exception as e:
    logger.error(f"图片验证码处理失败: {e}")
    raise

# 登录
logger.info("点击登录按钮...")
try:
    browser.ele('xpath://html/body/table/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr[3]/td[3]/input',
                timeout=5).click()
    time.sleep(2)
    logger.info("登录按钮点击成功")
except Exception as e:
    logger.error(f"登录按钮点击失败: {e}")
    raise

# 验证码
logger.info("获取短信验证码...")
try:
    browser.ele('xpath://*[@id="verify_code"]', timeout=5).click()
    mail_time = datetime.now()
    email_tool = Email189VerificationTool()
    result = email_tool.get_verification_code("IM运营平台", mail_time)
    email_code = browser.ele('xpath://*[@id="loginName"]')
    logger.info(f"获取到 短信验证码 为: {result}")
    email_code.input(result)
    time.sleep(1)
    browser.ele('xpath://*[@id="login_in"]').click()
    time.sleep(10)
    logger.info("短信验证码处理成功")
except Exception as e:
    logger.error(f"短信验证码处理失败: {e}")
    raise

# 页面操作
logger.info("登录成功，开始进行页面操作...")
try:
    browser.ele('xpath://*[@id="btn"]', timeout=5).click()
    time.sleep(5)
    browser.ele('xpath://*[@id="firstMenuItem_148"]', timeout=5).click()
    time.sleep(8)
    logger.info("页面操作导航成功")
except Exception as e:
    logger.error(f"页面操作导航失败: {e}")
    raise

# 打开 IM会话服务报表
logger.info("打开IM会话服务报表...")
try:
    browser.ele('xpath://*[@id="dcmsTree_1481"]/div[1]/a[2]', timeout=5).click()
    time.sleep(2)
    browser.ele('xpath://*[@id="dcmsTree_1482"]/div[1]/a[2]', timeout=5).click()
    time.sleep(2)
    browser.ele('xpath://*[@id="scmsTree_14894"]', timeout=5).click()
    time.sleep(2)
    logger.info("IM会话服务报表打开成功")
except Exception as e:
    logger.error(f"IM会话服务报表打开失败: {e}")
    raise

# 打开 远程柜台会话服务报表
logger.info("打开远程柜台会话服务报表...")
try:
    browser.ele('xpath://*[@id="dcmsTree_1482"]/div[9]/a[2]', timeout=5).click()
    time.sleep(2)
    browser.ele('xpath://*[@id="scmsTree_148118"]', timeout=5).click()
    time.sleep(2)
    logger.info("远程柜台会话服务报表打开成功")
except Exception as e:
    logger.error(f"远程柜台会话服务报表打开失败: {e}")
    raise

logger.info("页面导航完成，开始执行主要功能...")
try:
    IM_porttation_main()
    logger.info("主要功能执行成功")
except Exception as e:
    logger.error(f"主要功能执行失败: {e}")
    raise

# 关闭浏览器
logger.info("程序执行完成，关闭浏览器...")
try:
    browser.close()
    logger.info("浏览器关闭成功")
except Exception as e:
    logger.error(f"浏览器关闭失败: {e}")

time.sleep(20)
