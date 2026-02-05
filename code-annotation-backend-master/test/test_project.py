from test.db_helper import clean

clean()

# ----------------------------------------------------------

# 创建表，需要先创建user表
from db.db_user import UserDB

user_db = UserDB()

user_db.add_user("test", "test")

from db.db_project import ProjectDB

project_db = ProjectDB()

# === 在下面编写测试用例 ===

print(project_db.add_project("test", "test", 0, 0, 1))


# 使用selectall方法查询数据库的内容
print(project_db.selectall())
