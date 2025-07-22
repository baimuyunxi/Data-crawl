#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import threading
import time

import schedule
from DrissionPage import Chromium

from src.intelligent.navigation import main as navigation_main
from src.region.importtation import main as import_main
from src.region.transporttation import main as transport_main

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transport_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TransportScheduler:
    # 标签页配置
    TAB_CONFIGS = [
        '10000号运营管理平台',
        '高频呼入统计报表',
        '运营管理系统'
    ]

    # 刷新时间点配置（分钟）
    REFRESH_MINUTES = [0, 20, 40]

    def __init__(self):
        self.browser = None
        self.is_first_run = True
        self.is_running = False
        self.tab_check_thread = None

    def init_browser(self):
        """初始化浏览器"""
        try:
            logger.info("正在启动浏览器...")
            self.browser = Chromium()
            logger.info("浏览器启动成功")
            return True
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            return False

    def wait_and_first_run(self):
        """首次运行：启动浏览器，等待5分钟后执行"""
        if not self.is_first_run:
            return

        logger.info("首次运行 - 启动浏览器并等待5分钟...")

        # 启动浏览器
        if not self.init_browser():
            logger.error("首次启动浏览器失败，程序退出")
            return

        # 等待5分钟
        logger.info("等待5分钟后开始执行transportation...")
        time.sleep(300)  # 5分钟 = 300秒

        # 执行transportation
        self.execute_transportation()

        # 标记首次运行完成
        self.is_first_run = False
        logger.info("首次运行完成")

        # 启动标签页检测线程
        self.start_tab_monitoring()

    def execute_task(self, task_name, task_func):
        """执行单个任务的通用方法"""
        try:
            logger.info(f"开始执行{task_name}任务...")
            result = task_func()
            if result is not None:
                logger.info(f"{task_name}任务执行成功")
            else:
                logger.warning(f"{task_name}任务执行失败")
        except Exception as e:
            logger.error(f"执行{task_name}任务时发生错误: {e}")

    def execute_transportation(self):
        """执行所有transportation相关任务"""
        # 按顺序执行三个任务
        tasks = [
            ("transportation", transport_main),
            ("importtation", import_main),
            ("navigation", navigation_main)
        ]

        for task_name, task_func in tasks:
            self.execute_task(task_name, task_func)

    def check_and_refresh_tab_by_title(self, title):
        """通用的标签页检测和刷新方法"""
        if not self.browser:
            logger.warning("浏览器未初始化，无法检测标签页")
            return False

        try:
            tab = self.browser.get_tab(title=title)
            if tab:
                logger.info(f"检测到{title}标签页，执行刷新...")
                tab.refresh()
                logger.info(f"{title}标签页刷新完成")
                time.sleep(5)  # 等待页面加载
                return True
            else:
                logger.warning(f"未找到目标标签页: '{title}'")
                return False
        except Exception as e:
            logger.error(f"检测或刷新{title}标签页时发生错误: {e}")
            return False

    def refresh_all_tabs(self):
        """刷新所有配置的标签页"""
        for tab_title in self.TAB_CONFIGS:
            self.check_and_refresh_tab_by_title(tab_title)

    def get_next_refresh_time(self):
        """计算下次刷新时间（00、20、40分）"""
        now = datetime.datetime.now()
        current_minute = now.minute

        # 找到下一个刷新时间点
        next_minute = None
        for minute in self.REFRESH_MINUTES:
            if current_minute < minute:
                next_minute = minute
                break

        if next_minute is None:
            # 如果当前时间已经超过了所有刷新点，则下一次刷新是下一小时的第一个点
            next_minute = self.REFRESH_MINUTES[0]
            next_hour = now.hour + 1
            if next_hour >= 24:
                next_hour = 0
        else:
            next_hour = now.hour

        # 构造下次刷新时间
        next_refresh = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_minute == 0 and current_minute >= 40:
            next_refresh = next_refresh.replace(hour=next_hour)
            if next_hour == 0:
                next_refresh = next_refresh + datetime.timedelta(days=1)

        return next_refresh

    def tab_monitoring_loop(self):
        """标签页监控循环（每小时00、20、40分刷新）"""
        while True:
            try:
                # 计算下次刷新时间
                next_refresh = self.get_next_refresh_time()
                logger.info(f"下次标签页刷新时间: {next_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

                # 等待到下次刷新时间
                while datetime.datetime.now() < next_refresh:
                    time.sleep(1)

                current_time = datetime.datetime.now()
                logger.info(f"执行定时标签页刷新 - 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                self.refresh_all_tabs()

            except Exception as e:
                logger.error(f"标签页监控循环中发生错误: {e}")
                time.sleep(60)  # 发生错误时等待1分钟后重试

    def start_tab_monitoring(self):
        """启动标签页监控线程"""
        if self.tab_check_thread and self.tab_check_thread.is_alive():
            logger.info("标签页监控线程已在运行")
            return

        logger.info("启动标签页监控线程（每小时00、20、40分刷新）...")
        self.tab_check_thread = threading.Thread(target=self.tab_monitoring_loop, daemon=True)
        self.tab_check_thread.start()

    def daily_transportation_job(self):
        """每日9:05执行的transportation任务"""
        logger.info("执行每日9:05定时任务...")

        # 确保浏览器已启动
        if not self.browser:
            if not self.init_browser():
                logger.error("浏览器启动失败，跳过本次任务")
                return

        # 先刷新所有标签页
        self.refresh_all_tabs()

        # 执行transportation
        self.execute_transportation()

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.info("调度器已在运行")
            return

        self.is_running = True
        logger.info("启动定时任务调度器...")

        # 设置每日09:05的定时任务
        schedule.every().day.at("09:05").do(self.daily_transportation_job)
        logger.info("已设置每日09:05定时任务")

        # 如果是首次运行，执行首次启动流程
        if self.is_first_run:
            # 在单独线程中执行首次运行
            first_run_thread = threading.Thread(target=self.wait_and_first_run, daemon=True)
            first_run_thread.start()
        else:
            # 如果不是首次运行，直接启动标签页监控
            self.start_tab_monitoring()

        # 运行调度器主循环
        logger.info("定时任务调度器开始运行...")
        while True:
            schedule.run_pending()
            time.sleep(1)


def main():
    """主函数"""
    logger.info("=== 定时任务管理器启动 ===")
    logger.info(f"当前时间: {datetime.datetime.now()}")
    logger.info("任务配置:")
    logger.info("- 首次运行: 启动浏览器，等待5分钟后执行第一次试运行")
    logger.info("- 标签页监控: 每小时00、20、40分检测并刷新指定标签页")
    logger.info("- 定时任务: 每日9:05自动执行")
    logger.info("=" * 50)

    # 创建调度器实例
    scheduler = TransportScheduler()

    # 启动调度器
    scheduler.start_scheduler()


if __name__ == '__main__':
    main()
