from app.ArchTag import ArchTag
from flask import jsonify, request


from utils.token import token_required
from db.db_archTag import ArchTagDB
from db.db_file import FileDB
from db.db_relation import RelationDB
from db.db_user import UserDB

archTag_db = ArchTagDB()
file_db = FileDB()
relation_db = RelationDB()
user_db = UserDB()


@ArchTag.route("/modify", methods=["POST"])
@token_required
def modify_arch_tag(user_id: int):
    # ===  1. 获取当前打开的文件的路径，要修改的行位置，要移除的标签名，要修改成的标签名字和颜色
    file_path = request.form.get("file_path")
    if not file_path:
        return (
            jsonify(
                {"state": "fail", "description": "需要提供当前打开文件路径", "rst": {}}
            ),
            400,
        )

    line = request.form.get("line")
    if not line:
        return (
            jsonify({"state": "fail", "description": "需要提供当前行位置", "rst": {}}),
            400,
        )
    line = int(line)

    remove_tag_text = request.form.get("remove_tag_text")
    if remove_tag_text is None:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "需要提供要删除的标签名字，如果没有删除，那么需要提供一个空的字符串",
                    "rst": {},
                }
            ),
            400,
        )
    arch_tag_text = request.form.get("arch_tag_text")
    if not arch_tag_text:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "需要提供要修改成的标签名字",
                    "rst": {},
                }
            ),
            400,
        )
    arch_tag_color = request.form.get("arch_tag_color")
    if not arch_tag_color:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "需要提供要修改成的标签颜色",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 将新的标签名添加到关系表中，并且设置标签属性
    relation_db.add_arch_name(
        arch_tag_text
    )  # 不检查add_arch_name的返回值，因为如果已存在就不修改
    if not archTag_db.get_arch_tag_id(arch_tag_text, user_id):
        archTag_db.add_arch_tag(arch_tag_text, arch_tag_color, user_id)
    else:
        if not archTag_db.update_arch_tag(arch_tag_text, arch_tag_color):
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "修改标签属性失败",
                        "rst": {},
                    }
                ),
                400,
            )

    # === 3. 获取当前文件id，修改对应的relation
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "当前用户没有打开项目",
                    "rst": {},
                }
            ),
            400,
        )
    file_id = file_db.get_file_id_by_file_path(file_path, opened_project_id)
    if not file_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "当前文件不存在",
                    "rst": {},
                }
            ),
            400,
        )

    if remove_tag_text != arch_tag_text:
        if remove_tag_text:
            if not relation_db.update_relation_arch_value(
                file_id, opened_project_id, line, remove_tag_text, 0
            ):
                return (
                    jsonify(
                        {
                            "state": "fail",
                            "description": "修改旧标签值失败",
                            "rst": {},
                        }
                    ),
                    400,
                )
        if not relation_db.update_relation_arch_value(
            file_id, opened_project_id, line, arch_tag_text, 1
        ):
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "修改新标签值失败",
                        "rst": {},
                    }
                ),
                400,
            )

    # === 4. 获取当前行关系然后返回 ===
    relation = relation_db.get_relation_include_line(file_id, opened_project_id, line)
    if relation is None:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "当前行没有绑定关系",
                    "rst": {},
                }
            ),
            400,
        )

    return jsonify(
        {
            "state": "success",
            "description": "修改标签成功",
            "rst": {"start": relation["start"], "end": relation["end"]},
        }
    )
