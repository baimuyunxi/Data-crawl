import logging
import time

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

# 配置日志记录器
logger = logging.getLogger(__name__)


class OperatePgsql(object):
    def __init__(
            self,
            host="134.175.152.94",
            port=18921,
            user="dcm",
            password="O_xlZypKEygR78Kt",
            db="postgres",
            cursorclass=RealDictCursor,
    ):
        # 只保存连接参数，不立即建立连接
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.cursorclass = cursorclass
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）

        logger.info("数据库连接配置已初始化，将在需要时建立连接")

    def _create_connection(self):
        """创建新的数据库连接"""
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db,
                connect_timeout=10,  # 连接超时10秒
                application_name="DataCollector"  # 应用名称，便于监控
            )
            logger.debug("数据库连接创建成功")
            return connection
        except Exception as e:
            logger.error(f"数据库连接创建失败: {e}")
            raise

    def _execute_with_retry(self, operation_func, *args, **kwargs):
        """带重试机制的操作执行"""
        last_exception = None

        for attempt in range(self.max_retries):
            connection = None
            try:
                # 每次尝试都创建新连接
                connection = self._create_connection()

                # 执行操作
                result = operation_func(connection, *args, **kwargs)

                # 操作成功，返回结果
                return result

            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_exception = e
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")

                if attempt < self.max_retries - 1:
                    # 等待后重试
                    delay = self.retry_delay * (attempt + 1)  # 递增延迟
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"所有重试都失败了，最后的错误: {e}")
                    break

            except Exception as e:
                # 其他类型的错误，不重试
                logger.error(f"操作执行失败（非连接问题）: {e}")
                last_exception = e
                break
            finally:
                # 确保连接被关闭
                if connection and not connection.closed:
                    try:
                        connection.close()
                        logger.debug("数据库连接已关闭")
                    except Exception as close_error:
                        logger.warning(f"关闭连接时出错: {close_error}")

        # 如果所有重试都失败了，抛出最后的异常
        if last_exception:
            raise last_exception
        else:
            raise Exception("操作失败，原因未知")

    def _do_insert_data(self, connection, df, table_name):
        """实际执行插入操作的函数"""
        cursor = None
        try:
            cursor = connection.cursor()

            # 准备列名
            cols = [str(i) for i in df.columns.tolist()]
            cols_str = ",".join(cols)

            # 准备值
            values = [tuple(x) for x in df.to_numpy()]

            # 构建更新部分的 SQL：只更新 DataFrame 中除 p_day_id 外的字段
            update_fields = [col for col in cols if col != 'p_day_id']
            update_stmt = ",".join([
                f"{field} = EXCLUDED.{field}"
                for field in update_fields
            ])

            # 首先尝试获取已存在的 p_day_id 数量
            call_ids = [row[df.columns.get_loc('p_day_id')] for row in values]
            check_sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE p_day_id = ANY(%s)
            """
            cursor.execute(check_sql, (call_ids,))
            existing_count = cursor.fetchone()[0]
            new_count = len(values) - existing_count

            # 构建完整的 SQL 语句
            sql = f"""
                INSERT INTO {table_name} ({cols_str}) 
                VALUES %s 
                ON CONFLICT (p_day_id) 
                DO UPDATE SET {update_stmt}
                RETURNING (xmax = 0) AS inserted
            """

            # 执行插入
            execute_values(cursor, sql, values)

            # 提交事务
            connection.commit()
            logger.info(f"数据操作完成: 插入 {new_count} 条新记录，更新 {existing_count} 条已有记录")

            return new_count, existing_count

        except Exception as e:
            logger.error(f"数据操作异常: {e}")
            if connection and not connection.closed:
                connection.rollback()
            raise  # 重新抛出异常，让重试机制处理
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as cursor_error:
                    logger.warning(f"关闭游标时出错: {cursor_error}")

    def insert_data(self, df, table_name):
        """
        插入数据到数据库表，遇到重复的 p_day_id 时更新 DataFrame 中存在的字段
        采用按需连接方式，每次操作都创建新连接并在完成后关闭

        Args:
            df: 待插入的 DataFrame
            table_name: 目标表名

        Returns:
            tuple: (插入的行数, 更新的行数)
        """
        try:
            logger.info(f"开始插入数据到表 {table_name}，共 {len(df)} 行数据")
            result = self._execute_with_retry(self._do_insert_data, df, table_name)
            logger.info(f"数据插入操作完成")
            return result
        except Exception as e:
            logger.error(f"数据插入最终失败: {e}")
            return 0, 0

    def test_connection(self):
        """测试数据库连接是否正常"""
        try:
            connection = self._create_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def close(self):
        """
        关闭数据库连接（在按需连接模式下，此方法主要用于兼容性）
        """
        logger.info("按需连接模式下，连接会在每次操作后自动关闭")

    def __del__(self):
        """析构函数（在按需连接模式下无需特殊处理）"""
        pass
