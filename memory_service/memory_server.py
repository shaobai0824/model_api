import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 添加當前目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import JSONMemoryBackend, MemoryManager

# 載入環境變數
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# 設定日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(
    title="Memory Service",
    description="提供聊天記憶管理的 API",
    version="1.0.0",
)

# 全域記憶管理器
memory_manager: Optional[MemoryManager] = None


# Pydantic 模型
class AddMessageRequest(BaseModel):
    user_id: str
    role: str  # "user" 或 "assistant"
    content: str
    message_type: str = "text"


class SetPreferenceRequest(BaseModel):
    user_id: str
    key: str
    value: str


class UserIdRequest(BaseModel):
    user_id: str


@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化記憶管理器"""
    global memory_manager
    logger.info("正在初始化記憶服務...")

    try:
        # 設定記憶存儲目錄
        memory_data_dir = os.getenv("MEMORY_DATA_DIR", "memory_data")
        max_messages = int(os.getenv("MAX_MESSAGES_PER_USER", "50"))
        max_context = int(os.getenv("MAX_CONTEXT_MESSAGES", "10"))
        expire_days = int(os.getenv("MEMORY_EXPIRE_DAYS", "30"))

        # 初始化 JSON 後端和記憶管理器
        backend = JSONMemoryBackend(data_dir=memory_data_dir)
        memory_manager = MemoryManager(
            backend=backend,
            max_messages_per_user=max_messages,
            max_context_messages=max_context,
            memory_expire_days=expire_days,
        )

        logger.info("記憶服務初始化完成！")

    except Exception as e:
        logger.error(f"記憶服務啟動失敗: {e}", exc_info=True)
        raise


@app.get("/")
def read_root():
    return {"message": "Memory Service is running"}


@app.get("/health")
def health_check():
    """健康檢查"""
    if memory_manager is None:
        return {"status": "error", "message": "記憶管理器尚未初始化"}

    return {
        "status": "healthy",
        "backend": "JSON",
        "max_messages_per_user": memory_manager.max_messages_per_user,
        "max_context_messages": memory_manager.max_context_messages,
        "memory_expire_days": memory_manager.memory_expire_days,
    }


@app.post("/add_message")
async def add_message(request: AddMessageRequest):
    """添加訊息到用戶記憶"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        success = await memory_manager.add_message(
            user_id=request.user_id,
            role=request.role,
            content=request.content,
            message_type=request.message_type,
        )

        if success:
            return {"success": True, "message": "訊息已添加到記憶"}
        else:
            raise HTTPException(status_code=500, detail="添加訊息失敗")

    except Exception as e:
        logger.error(f"添加訊息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"添加訊息失敗: {str(e)}")


@app.get("/conversation_context/{user_id}")
async def get_conversation_context(user_id: str, include_system_prompt: bool = True):
    """獲取用戶的對話上下文"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        context = await memory_manager.get_conversation_context(
            user_id=user_id, include_system_prompt=include_system_prompt
        )

        return {
            "success": True,
            "user_id": user_id,
            "context": context,
            "message_count": len(context),
        }

    except Exception as e:
        logger.error(f"獲取對話上下文失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取對話上下文失敗: {str(e)}")


@app.get("/user_stats/{user_id}")
async def get_user_stats(user_id: str):
    """獲取用戶統計資訊"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        stats = await memory_manager.get_user_stats(user_id)
        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"獲取用戶統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取用戶統計失敗: {str(e)}")


@app.post("/clear_memory")
async def clear_user_memory(request: UserIdRequest):
    """清除用戶記憶"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        success = await memory_manager.clear_user_memory(request.user_id)

        if success:
            return {"success": True, "message": f"已清除用戶 {request.user_id} 的記憶"}
        else:
            raise HTTPException(status_code=500, detail="清除記憶失敗")

    except Exception as e:
        logger.error(f"清除記憶失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清除記憶失敗: {str(e)}")


@app.post("/set_preference")
async def set_user_preference(request: SetPreferenceRequest):
    """設定用戶偏好"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        success = await memory_manager.set_user_preference(
            user_id=request.user_id, key=request.key, value=request.value
        )

        if success:
            return {"success": True, "message": f"已設定用戶偏好 {request.key}"}
        else:
            raise HTTPException(status_code=500, detail="設定偏好失敗")

    except Exception as e:
        logger.error(f"設定偏好失敗: {e}")
        raise HTTPException(status_code=500, detail=f"設定偏好失敗: {str(e)}")


@app.post("/cleanup_expired")
async def cleanup_expired_memories():
    """清理過期記憶"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        expired_count = await memory_manager.cleanup_expired_memories()
        return {
            "success": True,
            "message": f"已清理 {expired_count} 個過期用戶記憶",
            "expired_count": expired_count,
        }

    except Exception as e:
        logger.error(f"清理過期記憶失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理過期記憶失敗: {str(e)}")


@app.get("/list_users")
async def list_users():
    """列出所有用戶"""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="記憶管理器尚未初始化")

    try:
        users = await memory_manager.backend.list_users()
        return {"success": True, "users": users, "user_count": len(users)}

    except Exception as e:
        logger.error(f"列出用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出用戶失敗: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("MEMORY_SERVICE_PORT", "8004"))
    uvicorn.run(app, host="0.0.0.0", port=port)
