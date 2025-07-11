#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import threading
import time

import schedule
from DrissionPage import Chromium

from src.importtation import main as import_main  # 新增导入
from src.transporttation import main as transport_main

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
    def __init__(self):
        self.browser = None
        self.is_first_run = True
        self.is_running = False
        self.tab_check_thread = None
        self.stop_flag = False

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

    def execute_transportation(self):
        """执行transportation任务"""
        try:
            logger.info("开始执行transportation任务...")
            result = transport_main()
            if result is not None:
                logger.info("transportation任务执行成功")
            else:
                logger.warning("transportation任务执行失败")
        except Exception as e:
            logger.error(f"执行transportation任务时发生错误: {e}")

        # 执行完transportation后，立即执行importtation
        try:
            logger.info("开始执行importtation任务...")
            result = import_main()
            if result is not None:
                logger.info("importtation任务执行成功")
            else:
                logger.warning("importtation任务执行失败")
        except Exception as e:
            logger.error(f"执行importtation任务时发生错误: {e}")

    def check_and_refresh_tab(self):
        """检测标签页并刷新"""
        if not self.browser:
            logger.warning("浏览器未初始化，无法检测标签页")
            return False

        try:
            # 尝试获取指定标签页
            tab = self.browser.get_tab(title='10000号运营管理平台')
            if tab:
                logger.info("检测到目标标签页，执行刷新...")
                tab.refresh()
                logger.info("标签页刷新完成")
                time.sleep(5)  # 等待页面加载
                return True
            else:
                logger.warning("未找到目标标签页: '10000号运营管理平台'")
                return False
        except Exception as e:
            logger.error(f"检测或刷新标签页时发生错误: {e}")
            return False

    def tab_monitoring_loop(self):
        """标签页监控循环（每20分钟执行一次）"""
        while not self.stop_flag:
            try:
                # 等待20分钟
                for _ in range(1200):  # 20分钟 = 1200秒
                    if self.stop_flag:
                        break
                    time.sleep(1)

                if not self.stop_flag:
                    self.check_and_refresh_tab()

            except Exception as e:
                logger.error(f"标签页监控循环中发生错误: {e}")
                time.sleep(60)  # 发生错误时等待1分钟后重试

    def start_tab_monitoring(self):
        """启动标签页监控线程"""
        if self.tab_check_thread and self.tab_check_thread.is_alive():
            logger.info("标签页监控线程已在运行")
            return

        logger.info("启动标签页监控线程（每20分钟刷新一次）...")
        self.tab_check_thread = threading.Thread(target=self.tab_monitoring_loop, daemon=True)
        self.tab_check_thread.start()

    def daily_transportation_job(self):
        """每日8:00执行的transportation任务"""
        logger.info("执行每日8:00定时任务...")

        # 确保浏览器已启动
        if not self.browser:
            if not self.init_browser():
                logger.error("浏览器启动失败，跳过本次任务")
                return

        # 先刷新标签页
        self.check_and_refresh_tab()

        # 执行transportation
        self.execute_transportation()

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.info("调度器已在运行")
            return

        self.is_running = True
        logger.info("启动定时任务调度器...")

        # 设置每日08:05的定时任务
        schedule.every().day.at("08:05").do(self.daily_transportation_job)
        logger.info("已设置每日08:05定时任务")

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
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在关闭调度器...")
            self.stop()
        except Exception as e:
            logger.error(f"调度器运行时发生错误: {e}")
            self.stop()

    def stop(self):
        """停止调度器"""
        logger.info("正在停止调度器...")
        self.stop_flag = True
        self.is_running = False

        # 等待线程结束
        if self.tab_check_thread and self.tab_check_thread.is_alive():
            logger.info("等待标签页监控线程结束...")
            self.tab_check_thread.join(timeout=5)

        # 关闭浏览器
        if self.browser:
            try:
                self.browser.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时发生错误: {e}")

        logger.info("调度器已停止")


def main():
    """主函数"""
    logger.info("=== 定时任务管理器启动 ===")
    logger.info(f"当前时间: {datetime.datetime.now()}")
    logger.info("任务配置:")
    logger.info("- 首次运行: 启动浏览器，等待5分钟后执行第一次试运行")
    logger.info("- 标签页监控: 每20分钟检测并刷新'10000号运营管理平台'标签页")
    logger.info("- 定时任务: 每日8:00自动执行")
    logger.info("=" * 50)

    # 创建调度器实例
    scheduler = TransportScheduler()

    try:
        # 启动调度器
        scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
    finally:
        # 确保清理资源
        scheduler.stop()


if __name__ == '__main__':
    main()
