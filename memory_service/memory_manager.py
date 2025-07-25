import asyncio
import json
import logging
import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """聊天訊息資料結構"""

    role: str  # "user" 或 "assistant"
    content: str
    timestamp: datetime
    message_type: str = "text"  # "text", "voice", "image" 等

    def to_dict(self) -> dict:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class UserMemory:
    """用戶記憶資料結構"""

    user_id: str
    messages: List[ChatMessage]
    preferences: Dict[str, any]
    last_interaction: datetime
    total_messages: int = 0

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "preferences": self.preferences,
            "last_interaction": self.last_interaction.isoformat(),
            "total_messages": self.total_messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserMemory":
        return cls(
            user_id=data["user_id"],
            messages=[ChatMessage.from_dict(msg) for msg in data["messages"]],
            preferences=data["preferences"],
            last_interaction=datetime.fromisoformat(data["last_interaction"]),
            total_messages=data.get("total_messages", 0),
        )


class MemoryBackend(ABC):
    """記憶存儲後端抽象類"""

    @abstractmethod
    async def save_user_memory(self, memory: UserMemory) -> bool:
        pass

    @abstractmethod
    async def load_user_memory(self, user_id: str) -> Optional[UserMemory]:
        pass

    @abstractmethod
    async def delete_user_memory(self, user_id: str) -> bool:
        pass

    @abstractmethod
    async def list_users(self) -> List[str]:
        pass


class JSONMemoryBackend(MemoryBackend):
    """JSON 檔案記憶後端"""

    def __init__(self, data_dir: str = "memory_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        logger.info(f"JSON 記憶後端初始化，資料目錄: {self.data_dir}")

    def _get_user_file(self, user_id: str) -> Path:
        # 使用安全的檔名
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ("-", "_"))
        return self.data_dir / f"user_{safe_user_id}.json"

    async def save_user_memory(self, memory: UserMemory) -> bool:
        try:
            file_path = self._get_user_file(memory.user_id)
            with self._lock:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"已儲存用戶 {memory.user_id} 的記憶")
            return True
        except Exception as e:
            logger.error(f"儲存用戶記憶失敗: {e}")
            return False

    async def load_user_memory(self, user_id: str) -> Optional[UserMemory]:
        try:
            file_path = self._get_user_file(user_id)
            if not file_path.exists():
                return None

            with self._lock:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            memory = UserMemory.from_dict(data)
            logger.debug(
                f"已載入用戶 {user_id} 的記憶，包含 {len(memory.messages)} 條訊息"
            )
            return memory
        except Exception as e:
            logger.error(f"載入用戶記憶失敗: {e}")
            return None

    async def delete_user_memory(self, user_id: str) -> bool:
        try:
            file_path = self._get_user_file(user_id)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"已刪除用戶 {user_id} 的記憶")
            return True
        except Exception as e:
            logger.error(f"刪除用戶記憶失敗: {e}")
            return False

    async def list_users(self) -> List[str]:
        try:
            users = []
            for file_path in self.data_dir.glob("user_*.json"):
                # 從檔名提取用戶 ID
                filename = file_path.stem
                if filename.startswith("user_"):
                    user_id = filename[5:]  # 移除 "user_" 前綴
                    users.append(user_id)
            return users
        except Exception as e:
            logger.error(f"列出用戶失敗: {e}")
            return []


class MemoryManager:
    """記憶管理器"""

    def __init__(
        self,
        backend: MemoryBackend,
        max_messages_per_user: int = 50,
        max_context_messages: int = 10,
        memory_expire_days: int = 30,
    ):
        self.backend = backend
        self.max_messages_per_user = max_messages_per_user
        self.max_context_messages = max_context_messages
        self.memory_expire_days = memory_expire_days
        self._cache: Dict[str, UserMemory] = {}
        self._cache_lock = threading.Lock()
        logger.info("記憶管理器初始化完成")

    async def add_message(
        self, user_id: str, role: str, content: str, message_type: str = "text"
    ) -> bool:
        """添加新訊息到用戶記憶"""
        try:
            # 載入或創建用戶記憶
            memory = await self._get_or_create_user_memory(user_id)

            # 添加新訊息
            new_message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                message_type=message_type,
            )

            memory.messages.append(new_message)
            memory.last_interaction = datetime.now()
            memory.total_messages += 1

            # 限制訊息數量
            if len(memory.messages) > self.max_messages_per_user:
                memory.messages = memory.messages[-self.max_messages_per_user :]

            # 更新快取和存儲
            with self._cache_lock:
                self._cache[user_id] = memory

            await self.backend.save_user_memory(memory)
            logger.debug(f"已為用戶 {user_id} 添加 {role} 訊息")
            return True

        except Exception as e:
            logger.error(f"添加訊息失敗: {e}")
            return False

    async def get_conversation_context(
        self, user_id: str, include_system_prompt: bool = True
    ) -> List[Dict[str, str]]:
        """獲取對話上下文，用於 LLM API"""
        try:
            memory = await self._get_or_create_user_memory(user_id)

            # 準備上下文訊息
            context_messages = []

            # 添加系統提示
            if include_system_prompt:
                context_messages.append(
                    {"role": "system", "content": self._generate_system_prompt(memory)}
                )

            # 添加最近的對話記錄
            recent_messages = memory.messages[-self.max_context_messages :]
            for msg in recent_messages:
                context_messages.append({"role": msg.role, "content": msg.content})

            logger.debug(
                f"為用戶 {user_id} 生成了包含 {len(context_messages)} 條訊息的上下文"
            )
            return context_messages

        except Exception as e:
            logger.error(f"獲取對話上下文失敗: {e}")
            return []

    async def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """獲取用戶統計資訊"""
        try:
            memory = await self._get_or_create_user_memory(user_id)

            # 計算統計資訊
            voice_messages = sum(
                1 for msg in memory.messages if msg.message_type == "voice"
            )
            text_messages = sum(
                1 for msg in memory.messages if msg.message_type == "text"
            )
            user_messages = sum(1 for msg in memory.messages if msg.role == "user")
            assistant_messages = sum(
                1 for msg in memory.messages if msg.role == "assistant"
            )

            return {
                "user_id": user_id,
                "total_messages": memory.total_messages,
                "current_session_messages": len(memory.messages),
                "voice_messages": voice_messages,
                "text_messages": text_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "last_interaction": memory.last_interaction.isoformat(),
                "preferences": memory.preferences,
            }

        except Exception as e:
            logger.error(f"獲取用戶統計失敗: {e}")
            return {}

    async def clear_user_memory(self, user_id: str) -> bool:
        """清除用戶記憶"""
        try:
            # 從快取中移除
            with self._cache_lock:
                self._cache.pop(user_id, None)

            # 從存儲中刪除
            await self.backend.delete_user_memory(user_id)
            logger.info(f"已清除用戶 {user_id} 的記憶")
            return True

        except Exception as e:
            logger.error(f"清除用戶記憶失敗: {e}")
            return False

    async def set_user_preference(self, user_id: str, key: str, value: any) -> bool:
        """設定用戶偏好"""
        try:
            memory = await self._get_or_create_user_memory(user_id)
            memory.preferences[key] = value

            with self._cache_lock:
                self._cache[user_id] = memory

            await self.backend.save_user_memory(memory)
            logger.debug(f"已為用戶 {user_id} 設定偏好 {key}={value}")
            return True

        except Exception as e:
            logger.error(f"設定用戶偏好失敗: {e}")
            return False

    async def cleanup_expired_memories(self) -> int:
        """清理過期記憶"""
        try:
            expired_count = 0
            cutoff_date = datetime.now() - timedelta(days=self.memory_expire_days)

            users = await self.backend.list_users()
            for user_id in users:
                memory = await self.backend.load_user_memory(user_id)
                if memory and memory.last_interaction < cutoff_date:
                    await self.backend.delete_user_memory(user_id)
                    expired_count += 1
                    logger.info(f"已清理過期用戶記憶: {user_id}")

            # 清理快取中的過期記憶
            with self._cache_lock:
                expired_users = [
                    user_id
                    for user_id, memory in self._cache.items()
                    if memory.last_interaction < cutoff_date
                ]
                for user_id in expired_users:
                    del self._cache[user_id]

            logger.info(f"記憶清理完成，共清理 {expired_count} 個過期用戶")
            return expired_count

        except Exception as e:
            logger.error(f"清理過期記憶失敗: {e}")
            return 0

    async def _get_or_create_user_memory(self, user_id: str) -> UserMemory:
        """獲取或創建用戶記憶"""
        # 先檢查快取
        with self._cache_lock:
            if user_id in self._cache:
                return self._cache[user_id]

        # 嘗試從存儲載入
        memory = await self.backend.load_user_memory(user_id)

        # 如果不存在，創建新的
        if memory is None:
            memory = UserMemory(
                user_id=user_id,
                messages=[],
                preferences={},
                last_interaction=datetime.now(),
                total_messages=0,
            )
            logger.info(f"為新用戶 {user_id} 創建記憶")

        # 更新快取
        with self._cache_lock:
            self._cache[user_id] = memory

        return memory

    def _generate_system_prompt(self, memory: UserMemory) -> str:
        """生成個性化系統提示"""
        base_prompt = """你是一個友善且有用的 AI 助手。你能夠記住我們之前的對話內容，並提供連貫的回應。"""

        # 根據用戶偏好和歷史調整提示
        if memory.preferences.get("language") == "formal":
            base_prompt += "請使用正式的語調回應。"
        elif memory.preferences.get("language") == "casual":
            base_prompt += "請使用輕鬆隨意的語調回應。"

        if memory.total_messages > 10:
            base_prompt += f"我們已經進行了 {memory.total_messages} 次對話。"

        return base_prompt
