import datetime as dt
import time

from DrissionPage import Chromium

from src.util.hw_util import select_time_province

print("浏览器配置完成，启动浏览器...")
try:
    browser = Chromium()
    print("浏览器启动成功")
except Exception as e:
    print(f"浏览器启动失败: {e}")
    raise

print("访问10000号运营管理平台...")
try:
    tab = browser.get_tab(title='10000号运营管理平台')
    time.sleep(5)
    print("网站访问成功")
except Exception as e:
    print(f"网站访问失败: {e}")
    raise

today = dt.date.today()
# 获取昨天日期
yesterday = today - dt.timedelta(days=1)
now_today = yesterday.strftime('%Y 年 %m 月 %d 日')
select_time_province(tab, now_today)
