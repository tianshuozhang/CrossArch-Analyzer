from db.db_mysql import DBc
from datetime import datetime


class UserDB(DBc):
    def __init__(
        self,
        host="localhost",
        user="root",
        password="123456",
        database="classify_c",
        port=3306,
        charset="utf8mb4",
    ):
        self.init_table_sql = """
        CREATE TABLE IF NOT EXISTS `users` (
            `id` BIGINT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE,
            `username` VARCHAR(50) NOT NULL UNIQUE,
            `password_hash` VARCHAR(255) NOT NULL,
            `created_time` DATETIME NOT NULL,
            `tmp_project_id` BIGINT NULL,
            `open_project_id` BIGINT DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        super().__init__(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset=charset,
            init_table_sql=self.init_table_sql,
        )

    def add_user(
        self,
        username: str,
        password_hash: str,
        tmp_project_id: int = 0,
        open_project_id: int = 0,
    ) -> int:
        """添加新用户，返回 user_id"""
        now = datetime.now()
        sql = "INSERT INTO users (username, password_hash, created_time, tmp_project_id, open_project_id) VALUES (%s, %s, %s, %s, %s)"
        self.execute(
            sql, (username, password_hash, now, tmp_project_id, open_project_id)
        )
        return self.cursor.lastrowid

    def username_exists(self, username: str) -> bool:
        """检查用户名是否已存在（注册时用）"""
        sql = "SELECT 1 FROM users WHERE username = %s"
        self.cursor.execute(sql, (username,))
        return self.cursor.fetchone() is not None

    def get_user_by_id(self, user_id: int) -> dict | None:
        """根据用户ID获取用户完整信息（用于鉴权和密码修改）"""
        sql = (
            "SELECT id, username, password_hash, created_time FROM users WHERE id = %s"
        )
        self.cursor.execute(sql, (user_id,))
        result = self.cursor.fetchone()
        return result if result else None

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """更新用户密码"""
        sql = "UPDATE users SET password_hash = %s WHERE id = %s"
        self.execute(sql, (new_password_hash, user_id))
        return self.cursor.rowcount > 0  # 返回是否成功更新

    def get_user_by_username(self, username: str) -> dict | None:
        """根据用户名获取用户完整信息（用于登录验证）"""
        sql = "SELECT id, username, password_hash, created_time FROM users WHERE username = %s"
        self.cursor.execute(sql, (username,))
        result = self.cursor.fetchone()
        return result if result else None

    def get_user_tmp_project_id(self, user_id: int) -> int | None:
        """获取用户的临时项目ID"""
        sql = "SELECT tmp_project_id FROM users WHERE id = %s"
        self.cursor.execute(sql, (user_id,))
        result = self.cursor.fetchone()
        return result["tmp_project_id"] if result else None

    def update_user_tmp_project_id(self, user_id: int, tmp_project_id: int) -> bool:
        """更新用户的临时项目ID"""
        sql = "UPDATE users SET tmp_project_id = %s WHERE id = %s"
        self.execute(sql, (tmp_project_id, user_id))
        return self.cursor.rowcount > 0  # 返回是否成功更新

    def get_user_open_project_id(self, user_id: int) -> int | None:
        """获取用户的打开项目ID"""
        sql = "SELECT open_project_id FROM users WHERE id = %s"
        self.cursor.execute(sql, (user_id,))
        result = self.cursor.fetchone()
        return result["open_project_id"] if result else None

    def update_user_open_project_id(self, user_id: int, open_project_id: int) -> bool:
        """更新用户的打开项目ID"""
        sql = "UPDATE users SET open_project_id = %s WHERE id = %s"
        self.execute(sql, (open_project_id, user_id))
        return self.cursor.rowcount > 0  # 返回是否成功更新
