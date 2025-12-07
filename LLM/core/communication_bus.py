from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import threading
from queue import Queue
import uuid
from datetime import datetime

class MessageType(Enum):
    """消息类型枚举"""
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result" 
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"

@dataclass
class AgentMessage:
    """Agent间通信消息"""
    message_id: str
    sender_id: str
    receiver_id: str  # "broadcast" 表示广播消息
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: float
    priority: int = 1  # 优先级 (1-10, 越高越优先)

class CommunicationBus:
    """通信总线：管理多Agent间的消息通信"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # 注册的Agent
        self.message_queues: Dict[str, Queue] = {}  # 各Agent的消息队列
        self.message_handlers: Dict[str, Callable] = {}  # 消息处理器
        self.running = False
        
    def register_agent(self, agent_id: str, agent_instance: Any):
        """注册Agent到通信总线"""
        self.agents[agent_id] = agent_instance
        self.message_queues[agent_id] = Queue()
        
    def send_message(self, message: AgentMessage):
        """发送消息到指定Agent"""
        if message.receiver_id == "broadcast":
            # 广播消息：发送给所有Agent
            for agent_id in self.agents:
                if agent_id != message.sender_id:  # 不发送给自己
                    self.message_queues[agent_id].put(message)
        else:
            # 单播消息
            if message.receiver_id in self.message_queues:
                self.message_queues[message.receiver_id].put(message)
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type.value] = handler
    
    def start(self):
        """启动通信总线"""
        self.running = True
        self._message_loop_thread = threading.Thread(target=self._message_processing_loop)
        self._message_loop_thread.daemon = True
        self._message_loop_thread.start()
    
    def _message_processing_loop(self):
        """消息处理循环"""
        while self.running:
            for agent_id, queue in self.message_queues.items():
                try:
                    # 非阻塞获取消息
                    message = queue.get_nowait()
                    
                    # 处理消息
                    if message.message_type.value in self.message_handlers:
                        handler = self.message_handlers[message.message_type.value]
                        handler(message)
                    else:
                        # 默认消息处理
                        print(f"🚦 默认处理消息: {message}")
                        self._default_message_handler(message)
                        
                    queue.task_done()
                    
                except:
                    continue
            
            # 短暂休眠避免CPU占用过高
            asyncio.sleep(0.1)
    
    def _default_message_handler(self, message: AgentMessage):
        """默认消息处理器"""
        agent = self.agents.get(message.receiver_id)
        if agent and hasattr(agent, 'handle_message'):
            agent.handle_message(message)
    
    def create_task_request(self, sender_id: str, task_type: str, 
                          task_data: Dict[str, Any], receiver_id: str) -> AgentMessage:
        """创建任务请求消息"""
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.TASK_REQUEST,
            content={
                "task_type": task_type,
                "task_data": task_data,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now().timestamp()
        )
