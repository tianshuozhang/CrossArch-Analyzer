# 需要提供的函数

## 架构标注分析函数

（from LLM.api import orchestrator）

orchestrator.analyze(project_root_path:str, task_id:int)
- project_root_path: 要分析的项目根目录的绝对路径
- task_id: 任务ID，过程中需要使用这个id更新任务进度，使用到的相关函数在CrossArch-Analyzer/code-annotation-backend-master/llm_tools/task.py

analyze需要返回的结果如下：

```JSON
{
    "report": "对项目的自然语言文字分析报告",
    "file_tag_data":[
        {
            "file_path": "项目根目录下的文件相对路径",
            "tag_data": [
                {
                    "start":123,
                    "end": 124,
                    "tag_name": ["架构名如","arm","x86","irrelevant"],
                }
            ]
        }
    ]
}
```

## 自然语言回答/可视化图数据生成函数

orchestrator.ask(question:str,project_root_path:str,user_id:int)
- question: 用户的问题
- project_root_path: 项目根目录的绝对路径
- user_id: 用户ID，用于访问数据库里的信息（之前的项目架构标注数据保存到了数据库），使用的相关函数可以参考CrossArch-Analyzer/code-annotation-backend-master/llm_tools/graph.py

ask需要返回的结果如下：

```JSON
{
    "response": "回答",
    "graph":{
        "title": "可视化图标题",
        "option":{
            // ECharts格式的可视化图option数据
        }
    }
}
```