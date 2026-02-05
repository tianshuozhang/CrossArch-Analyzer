from algo_framework.utils.state_manager import StateManager
from algo_framework.utils.memory_manager import MemoryManager
from algo_framework.utils.rela_path import resource_path

from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferWindowMemory
from datetime import datetime
from langchain_core.messages import BaseMessage
from typing import List


class report_Agent:
    def __init__(self, system_prompt: str, agent_id: str = "orchestrator_001"):
        self.system_prompt = system_prompt

        llm_config = {
            "model": "deepseek-v3:671b",  # 模型名称
            "openai_api_key": "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
            "openai_api_base": "https://uni-api.cstcloud.cn/v1",
            "temperature": 0.2,
        }
        self.llm = ChatOpenAI(**llm_config)
        self.state_manager = StateManager()
        # 1. 长期/事实记忆 (保留您的自定义 MemoryManager)
        # 负责存储分析结果、架构模式等结构化数据，用于语义检索。
        self.long_term_knowledge = MemoryManager(
            model_name=resource_path("../models/all-MiniLM-L6-v2")
        )

        # 2. 短期/会话记忆 (使用 LangChain ConversationBufferWindowMemory)
        # 负责存储和总结用户与 Orchestrator 之间的对话历史。
        self.session_memory = ConversationBufferWindowMemory(
            k=50,  # 存储最近50条消息
            memory_key="chat_history",  # 约定键名
            return_messages=True,  # 返回消息对象列表，便于构建 Prompt
        )
        self.agent_id = agent_id
        # 当前状态
        self.current_state = {
            "agent_id": self.agent_id,
            "current_session": self.session_memory,
            "last_analyzed_code": None,
            "last_analysis_result": None,
            "created_time": datetime.now().isoformat(),
        }
        self.load_agent_state()
        self.load_agent_memories()

    def get_response(self, user_prompt: str) -> str:

        context = self.build_context(user_prompt)
        response = self.llm.invoke(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": context},
            ]
        )
        self.current_state["last_analysis_result"] = response.content
        self.current_state["last_analyzed_code"] = user_prompt
        self.session_memory.save_context(
            {"input": user_prompt}, {"output": response.content}
        )
        self.long_term_knowledge.add_memory(
            importance=0.5,
            memory_type="analysis_result",
            content=response.content,
            metadata={"timestamp": datetime.now().isoformat(), "input": user_prompt},
        )
        self.save_agent_state()
        self.save_agent_memories()
        return response.content

    def load_agent_state(self, version: str = "latest", format_type: str = "json"):
        """加载Agent状态"""
        state = self.state_manager.load_state(self.agent_id, format_type, version)
        if state:
            self.current_state.update(state.get("current_state", {}))
            print("load existing agent state")  # 加载已有状态
            return True
        print("initialize new agent state")  # 初始化新状态
        return False

    def load_agent_memories(self, version: str = "latest", format_type: str = "json"):
        """加载Agent记忆"""
        return self.long_term_knowledge.load_memories(
            agent_id=self.agent_id, format_type=format_type, version=version
        )

    def save_agent_state(self, format_type: str = "json"):
        """保存Agent状态"""
        state_to_save = {
            "current_state": self.current_state,
            "memory_count": len(self.long_term_knowledge.memories),
            "last_saved": datetime.now().isoformat(),
        }

        return self.state_manager.save_state(self.agent_id, state_to_save, format_type)

    def build_context(self, user_prompt: str) -> str:
        memory_summary = self.long_term_knowledge.summarize_memories(max_tokens=3000)
        relevant_memories = self.long_term_knowledge.retrieve_relevant_memories(
            user_prompt,  # 使用语义更丰富的查询
            memory_type="analysis_result",
            top_k=3,  # 限制数量，保证相关性[5](@ref)
        )
        context_parts = []
        history_vars = self.session_memory.load_memory_variables({})
        chat_history_messages: List[BaseMessage] = history_vars.get("chat_history", [])

        if chat_history_messages:
            # 将 LangChain 的 Message 对象列表格式化为 Prompt 字符串
            formatted_history = "\n".join(
                [
                    f"[{msg.type.capitalize()}]: {msg.content}"
                    for msg in chat_history_messages
                ]
            )

            context_parts.append("【会话历史摘要】")
            context_parts.append(formatted_history)
            context_parts.append("###")
        # 长期记忆：将记忆摘要和相关记忆整合为上下文
        context_parts.append("【长期记忆摘要】")
        context_parts.append(memory_summary)
        context_parts.append("###")
        context_parts.append("【相关记忆】")
        context_parts.append(
            "\n".join([memory.content for memory in relevant_memories])
        )

        return "\n".join(context_parts)

    def save_agent_memories(self, format_type: str = "json"):
        """保存Agent记忆"""
        return self.long_term_knowledge.save_memories(
            agent_id=self.agent_id, format_type=format_type
        )


class rewrite_Agent:
    def __init__(self, system_prompt: str, agent_id: str = "orchestrator_001"):
        self.system_prompt = system_prompt

        llm_config = {
            "model": "deepseek-v3:671b",  # 模型名称
            "openai_api_key": "a21f78197ba7ada844c0479eb42459cf7be1a5cde7b57bc080e1123836654b23",
            "openai_api_base": "https://uni-api.cstcloud.cn/v1",
            "temperature": 0.2,
        }
        self.llm = ChatOpenAI(**llm_config)

    def get_response(self, user_prompt: str) -> str:

        response = self.llm.invoke(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return response.content
