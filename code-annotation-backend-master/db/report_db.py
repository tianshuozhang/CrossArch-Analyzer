from db.sqlite3_db import DB


class report_DB(DB):
    def __init__(self, db_path="data/code.sqlite"):
        self.db_path = db_path
        self.init_table_sql = """"""
        super(report_DB, self).__init__(self.db_path, self.init_table_sql)

    def selectOneReport(self, user_id, code_id) -> str | None:
        if True:
            return "报告内容"
        else:
            return None

    def oneUserAddReport(self, user_id, project_id, report_content):
        if True:
            return True
        else:
            return None
