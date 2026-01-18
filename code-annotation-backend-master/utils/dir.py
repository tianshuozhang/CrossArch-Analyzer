import shutil
import os


def process_dir_structure(target_dir: str):
    # 将target_dir规范成target_dir/content,target_dir/graph的结构
    try:
        dirs = os.listdir(target_dir)

        for dir in dirs:
            if dir == "content":
                continue
            if dir == "graph":
                continue
            shutil.rmtree(os.path.join(target_dir, dir))

        project_dir = os.path.join(target_dir, "content")
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        graph_dir = os.path.join(target_dir, "graph")
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
    except Exception as e:
        raise e
