#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import logging
import os
import sys
import time

import schedule

from src.register import Decision_system  # 新增导入
from src.register import IM_platform
# 导入需要执行的模块
from src.register import jt_zineng
from src.register import management

# 获取exe文件所在目录，确保日志文件在正确位置
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    base_dir = os.path.dirname(sys.executable)
else:
    # 如果是源码运行
    base_dir = os.path.dirname(os.path.abspath(__file__))

# 日志文件路径
log_file = os.path.join(base_dir, 'daily_scheduler.log')
transport_log_file = os.path.join(base_dir, 'transport_scheduler.log')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 添加一个专门的传输调度器日志
transport_logger = logging.getLogger('transport_scheduler')
transport_handler = logging.FileHandler(transport_log_file, encoding='utf-8')
transport_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
transport_logger.addHandler(transport_handler)
transport_logger.addHandler(logging.StreamHandler(sys.stdout))
transport_logger.setLevel(logging.INFO)


class DailyScheduler:
    def __init__(self):
        self.is_running = False
        self.task_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.decision_task_count = 0  # 新增决策系统任务计数器

    def execute_task(self, task_name, task_module):
        """执行单个任务的通用方法"""
        start_time = datetime.datetime.now()
        try:
            logger.info(f"开始执行{task_name}任务...")
            transport_logger.info(f"[任务开始] {task_name} - 开始时间: {start_time}")

            # 如果模块有main函数，调用main函数
            if hasattr(task_module, 'main'):
                result = task_module.main()
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()

                logger.info(f"{task_name}任务执行完成，耗时: {duration:.2f}秒")
                transport_logger.info(f"[任务完成] {task_name} - 结束时间: {end_time}, 耗时: {duration:.2f}秒")
                self.success_count += 1
                return True
            else:
                logger.warning(f"{task_name}模块没有main函数")
                transport_logger.warning(f"[任务错误] {task_name} - 模块没有main函数")
                self.failed_count += 1
                return False

        except Exception as e:
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = f"执行{task_name}任务时发生错误: {e}"

            logger.error(error_msg)
            transport_logger.error(f"[任务失败] {task_name} - 错误: {e}, 耗时: {duration:.2f}秒")
            self.failed_count += 1
            return False

    def daily_job(self):
        """每日8:10执行的任务"""
        job_start_time = datetime.datetime.now()
        self.task_count += 1
        self.success_count = 0
        self.failed_count = 0

        logger.info("=" * 80)
        logger.info(f"开始执行每日8:10定时任务 - 第{self.task_count}次执行")
        logger.info(f"当前时间: {job_start_time}")
        logger.info("=" * 80)

        transport_logger.info("=" * 80)
        transport_logger.info(f"[批次开始] 第{self.task_count}次定时任务批次 - {job_start_time}")
        transport_logger.info("=" * 80)

        # 按顺序执行三个任务
        tasks = [
            ("管理系统", management),
            ("IM平台", IM_platform),
            ("智能客服系统", jt_zineng)
        ]

        for i, (task_name, task_module) in enumerate(tasks, 1):
            logger.info(f"[{i}/{len(tasks)}] 准备执行: {task_name}")
            self.execute_task(task_name, task_module)

            # 任务间隔等待5秒（最后一个任务不需要等待）
            if i < len(tasks):
                logger.info(f"任务间隔等待5秒...")
                time.sleep(5)

        job_end_time = datetime.datetime.now()
        total_duration = (job_end_time - job_start_time).total_seconds()

        logger.info("=" * 80)
        logger.info(f"每日定时任务执行完成 - 成功: {self.success_count}/{len(tasks)}, 失败: {self.failed_count}")
        logger.info(f"总耗时: {total_duration:.2f}秒")
        logger.info("=" * 80)

        transport_logger.info("=" * 80)
        transport_logger.info(f"[批次完成] 第{self.task_count}次任务批次完成")
        transport_logger.info(f"成功: {self.success_count}, 失败: {self.failed_count}, 总耗时: {total_duration:.2f}秒")
        transport_logger.info("=" * 80)

    def decision_job(self):
        """每日15:10执行的决策系统任务"""
        job_start_time = datetime.datetime.now()
        self.decision_task_count += 1
        self.success_count = 0
        self.failed_count = 0

        logger.info("=" * 80)
        logger.info(f"开始执行每日15:10决策系统任务 - 第{self.decision_task_count}次执行")
        logger.info(f"当前时间: {job_start_time}")
        logger.info("=" * 80)

        transport_logger.info("=" * 80)
        transport_logger.info(f"[决策任务开始] 第{self.decision_task_count}次决策系统任务 - {job_start_time}")
        transport_logger.info("=" * 80)

        # 执行决策系统任务
        self.execute_task("决策系统", Decision_system)

        job_end_time = datetime.datetime.now()
        total_duration = (job_end_time - job_start_time).total_seconds()

        logger.info("=" * 80)
        logger.info(f"决策系统任务执行完成 - 成功: {self.success_count}, 失败: {self.failed_count}")
        logger.info(f"总耗时: {total_duration:.2f}秒")
        logger.info("=" * 80)

        transport_logger.info("=" * 80)
        transport_logger.info(f"[决策任务完成] 第{self.decision_task_count}次决策系统任务完成")
        transport_logger.info(f"成功: {self.success_count}, 失败: {self.failed_count}, 总耗时: {total_duration:.2f}秒")
        transport_logger.info("=" * 80)

    def get_next_run_time(self):
        """获取下次运行时间"""
        now = datetime.datetime.now()
        next_run = now.replace(hour=8, minute=10, second=0, microsecond=0)

        # 如果今天的8:10已经过了，则计算明天的8:10
        if next_run <= now:
            next_run += datetime.timedelta(days=1)

        return next_run

    def get_next_decision_run_time(self):
        """获取下次决策系统运行时间"""
        now = datetime.datetime.now()
        next_run = now.replace(hour=15, minute=10, second=0, microsecond=0)

        # 如果今天的15:10已经过了，则计算明天的15:10
        if next_run <= now:
            next_run += datetime.timedelta(days=1)

        return next_run

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.info("调度器已在运行")
            return

        self.is_running = True
        logger.info("启动定时任务调度器...")
        transport_logger.info(f"[系统启动] 传输调度器启动 - {datetime.datetime.now()}")

        # 设置每日08:10的定时任务
        schedule.every().day.at("08:10").do(self.daily_job)
        # 新增：设置每日15:10的决策系统定时任务
        schedule.every().day.at("15:10").do(self.decision_job)

        next_run = self.get_next_run_time()
        next_decision_run = self.get_next_decision_run_time()
        logger.info(f"已设置每日08:10定时任务，下次执行时间: {next_run}")
        logger.info(f"已设置每日15:10决策系统任务，下次执行时间: {next_decision_run}")

        # 显示系统信息
        logger.info("=" * 50)
        logger.info("系统信息:")
        logger.info(f"- 工作目录: {base_dir}")
        logger.info(f"- 日志文件: {log_file}")
        logger.info(f"- 传输日志: {transport_log_file}")
        logger.info(f"- Python版本: {sys.version}")
        logger.info(f"- 是否打包运行: {'是' if getattr(sys, 'frozen', False) else '否'}")
        logger.info("=" * 50)

        # 运行调度器主循环
        logger.info("定时任务调度器开始运行...")
        logger.info("按 Ctrl+C 停止程序")

        try:
            while True:
                schedule.run_pending()

                # 每小时显示一次状态信息
                current_time = datetime.datetime.now()
                if current_time.minute == 0 and current_time.second < 60:
                    next_run = self.get_next_run_time()
                    next_decision_run = self.get_next_decision_run_time()

                    time_until_next = next_run - current_time
                    hours = int(time_until_next.total_seconds() // 3600)
                    minutes = int((time_until_next.total_seconds() % 3600) // 60)

                    time_until_decision = next_decision_run - current_time
                    decision_hours = int(time_until_decision.total_seconds() // 3600)
                    decision_minutes = int((time_until_decision.total_seconds() % 3600) // 60)

                    logger.info(f"[状态检查] 当前时间: {current_time.strftime('%Y-%m-%d %H:%M')}")
                    logger.info(f"  距离8:10任务还有: {hours}小时{minutes}分钟")
                    logger.info(f"  距离15:10决策任务还有: {decision_hours}小时{decision_minutes}分钟")

                time.sleep(60)  # 每分钟检查一次

        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭调度器...")
            transport_logger.info(f"[系统关闭] 传输调度器关闭 - {datetime.datetime.now()}")
            self.is_running = False
        except Exception as e:
            logger.error(f"调度器运行时发生意外错误: {e}")
            transport_logger.error(f"[系统错误] 调度器异常: {e}")
            raise


def main():
    """主函数"""
    print("=" * 80)
    print("       中心监控脚本 - 每日定时任务管理器")
    print("=" * 80)

    logger.info("=== 每日定时任务管理器启动 ===")
    logger.info(f"启动时间: {datetime.datetime.now()}")
    logger.info("任务配置:")
    logger.info("- 执行时间1: 每日08:10")
    logger.info("- 执行顺序: jt_zineng.py -> management.py -> IM_platform.py")
    logger.info("- 任务间隔: 5秒")
    logger.info("- 执行时间2: 每日15:10")  # 新增任务说明
    logger.info("- 执行内容: Decision_system.py")  # 新增任务说明
    logger.info("=" * 50)

    # 创建调度器实例
    scheduler = DailyScheduler()

    try:
        # 启动调度器
        scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        input("按回车键退出...")
        sys.exit(1)


if __name__ == '__main__':
    main()
