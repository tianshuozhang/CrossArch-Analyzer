def clean():
    # ----------------------------------------------------------
    # 清除工作：删除所有的表
    import pymysql

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="classify_c",
        port=3306,
        charset="utf8mb4",
    )
    cursor = conn.cursor()
    sql = f"DROP TABLE IF EXISTS projects, users,arch_tags,files,line_attributes,modify_records,line_arch_tag_relations,tasks,visualization_data ;"
    cursor.execute(sql)

    conn.commit()
    cursor.close()
    conn.close()
