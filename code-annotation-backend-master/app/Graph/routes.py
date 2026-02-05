from flask import request, jsonify
import os, json

from app.Graph import Graph
from utils.token import token_required
from utils.path import *
from utils.zip import *

from db.db_visualData import VisualizationDataDB
from db.db_user import UserDB

user_db = UserDB()
graph_db = VisualizationDataDB()


@Graph.route("/get_list", methods=["POST"])
@token_required
def get_list(user_id: int):
    # === 1. 获取项目ID ===
    project_id = request.form.get("project_id")
    if not project_id:
        return (
            jsonify({"state": "fail", "description": "没有提供项目ID", "rst": {}}),
            400,
        )
    project_id = int(project_id)
    # === 2. 读取图数据的title并返回 ===
    graphs = graph_db.get_all_visualization_data_title_id_list(project_id)
    return (
        jsonify(
            {
                "state": "success",
                "description": "成功",
                "rst": {"graphs": graphs},
            }
        ),
        200,
    )


@Graph.route("/get_graph", methods=["POST"])
@token_required
def get_graph(user_id: int):
    # === 1. 获取用户要打开的图ID ===
    graph_id = request.form.get("graph_id")
    if not graph_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有提供图ID",
                    "rst": {},
                }
            ),
            400,
        )
    graph_id = int(graph_id)
    # === 2. 读取图文件数据 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有打开的项目",
                    "rst": {},
                }
            ),
            400,
        )

    graph_data_content = zip_read_file_from_zip(
        path_file_save_zip(user_id, opened_project_id),
        os.path.join("graph", f"{graph_id}.json"),
    )
    graph_data = json.loads(graph_data_content)

    # === 3. 返回图数据 ===

    return (
        jsonify(
            {
                "state": "success",
                "description": "成功",
                "rst": {"option": graph_data},
            }
        ),
        200,
    )
