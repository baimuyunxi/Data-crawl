import psycopg2
from psycopg2.extras import RealDictCursor, execute_values


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
        self.connection = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db,
        )
        self.cursorclass = cursorclass

    def insert_data(self, df, table_name):
        """
        插入数据到数据库表，遇到重复的 call_id 时更新 DataFrame 中存在的字段

        Args:
            df: 待插入的 DataFrame
            table_name: 目标表名

        Returns:
            tuple: (插入的行数, 更新的行数)
        """
        cursor = None
        try:
            cursor = self.connection.cursor()

            # 准备列名
            cols = [str(i) for i in df.columns.tolist()]
            cols_str = ",".join(cols)

            # 准备值
            values = [tuple(x) for x in df.to_numpy()]

            # 构建更新部分的 SQL：只更新 DataFrame 中除 call_id 外的字段
            update_fields = [col for col in cols if col != 'p_day_id']
            update_stmt = ",".join([
                f"{field} = EXCLUDED.{field}"
                for field in update_fields
            ])

            # 首先尝试获取已存在的 call_id 数量
            call_ids = [row[df.columns.get_loc('p_day_id')] for row in values]
            check_sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE call_id = ANY(%s)
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

            self.connection.commit()
            print(f"数据操作完成: 插入 {new_count} 条新记录，更新 {existing_count} 条已有记录")

            return new_count, existing_count

        except Exception as e:
            print(f"数据操作异常: {e}")
            self.connection.rollback()
            return 0, 0
        finally:
            if cursor:
                cursor.close()
