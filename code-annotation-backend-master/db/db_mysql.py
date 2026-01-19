import pymysql
from pymysql.cursors import DictCursor


def dict_factory(cursor, row):
    """保持与原来相同的字典工厂函数，但PyMySQL的DictCursor已经能返回字典"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DBc:
    def __init__(
        self,
        host="localhost",
        user="root",
        password="123456",
        database="classify_c",
        port=3306,
        charset="utf8mb4",
        init_table_sql="CREATE TABLE IF NOT EXISTS feeds (_id INT AUTO_INCREMENT PRIMARY KEY, url VARCHAR(255), title VARCHAR(255));",
        table_name="feeds",
    ):
        """
        初始化MySQL连接
        参数说明:
        host: MySQL主机地址
        user: root
        password: 123456
        database: 数据库名 classify_c
        port: 端口，默认3306
        charset: 字符集，默认utf8mb4
        init_table_sql: 初始化表的SQL语句
        """
        try:
            # 建立MySQL连接
            self.con = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                charset=charset,
                cursorclass=DictCursor,  # 使用DictCursor直接返回字典
                autocommit=False,  # 关闭自动提交，使用手动提交
            )
            self.cursor = self.con.cursor()
            self.table_name = table_name
            # 创建表
            if init_table_sql:
                self.cursor.execute(init_table_sql)
                self.con.commit()

        except pymysql.Error as e:
            print(f"数据库连接错误: {e}")
            raise

    def execute(self, sql, params=()):
        """执行SQL语句"""
        try:
            self.cursor.execute(sql, params)
            self.con.commit()
        except pymysql.Error as e:
            self.con.rollback()  # 出错时回滚
            print(f"SQL执行错误: {e}, SQL: {sql}, Params: {params}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.con:
            self.con.close()

    def insert(self, url, title):
        """插入数据"""
        # 注意：MySQL使用%s作为占位符，而不是?
        self.execute(
            f"INSERT INTO {self.table_name} (url, title) VALUES (%s, %s)", (url, title)
        )
        return self.cursor.lastrowid  # PyMySQL也支持lastrowid获取自增ID

    def delete(self, id):
        """删除数据"""
        # 使用参数化查询防止SQL注入
        self.execute(f"DELETE FROM {self.table_name} WHERE _id = %s", (id,))

    def selectall(self, where="1=1"):
        """查询所有数据"""
        # 注意：这里使用参数化查询
        sql = f"SELECT * FROM {self.table_name} WHERE {where}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def selectone(self, where="1=1"):
        """查询单条数据"""
        sql = f"SELECT * FROM {self.table_name} WHERE {where}"
        self.cursor.execute(sql)
        return self.cursor.fetchone()

    def clear(self):
        """清空表"""
        self.execute(f"DELETE FROM {self.table_name}")

    def __enter__(self):
        """支持with语句的上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接"""
        self.close()
