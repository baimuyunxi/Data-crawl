#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import time

import schedule

from src.register import IM_platform
# 导入需要执行的模块
from src.register import jt_zineng
from src.register import management

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DailyScheduler:
    def __init__(self):
        self.is_running = False

    def execute_task(self, task_name, task_module):
        """执行单个任务的通用方法"""
        try:
            logger.info(f"开始执行{task_name}任务...")
            # 如果模块有main函数，调用main函数
            if hasattr(task_module, 'main'):
                result = task_module.main()
            else:
                logger.warning(f"{task_name}模块没有main函数")
                return False

            logger.info(f"{task_name}任务执行完成")
            return True
        except Exception as e:
            logger.error(f"执行{task_name}任务时发生错误: {e}")
            return False

    def daily_job(self):
        """每日8:10执行的任务"""
        logger.info("=" * 60)
        logger.info(f"开始执行每日8:10定时任务 - 当前时间: {datetime.datetime.now()}")
        logger.info("=" * 60)

        # 按顺序执行三个任务
        tasks = [
            ("智能客服系统", jt_zineng),
            ("管理系统", management),
            ("IM平台", IM_platform)
        ]

        success_count = 0
        for task_name, task_module in tasks:
            if self.execute_task(task_name, task_module):
                success_count += 1

            # 任务间隔等待5秒
            time.sleep(5)

        logger.info("=" * 60)
        logger.info(f"每日定时任务执行完成 - 成功: {success_count}/{len(tasks)}")
        logger.info("=" * 60)

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.info("调度器已在运行")
            return

        self.is_running = True
        logger.info("启动定时任务调度器...")

        # 设置每日08:10的定时任务
        schedule.every().day.at("08:10").do(self.daily_job)
        logger.info("已设置每日08:10定时任务")

        # 运行调度器主循环
        logger.info("定时任务调度器开始运行...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次


def main():
    """主函数"""
    logger.info("=== 每日定时任务管理器启动 ===")
    logger.info(f"当前时间: {datetime.datetime.now()}")
    logger.info("任务配置:")
    logger.info("- 执行时间: 每日08:10")
    logger.info("- 执行任务: jt_zineng.py -> management.py -> IM_platform.py")
    logger.info("=" * 50)

    # 创建调度器实例
    scheduler = DailyScheduler()

    # 启动调度器
    scheduler.start_scheduler()


if __name__ == '__main__':
    main()
