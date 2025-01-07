"""Run Tarot Reader Application"""
import sys
import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tarot_service import TarotService

# 设置日志
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

def create_app():
    """创建 FastAPI 应用"""
    app = FastAPI()
    
    # 允许跨域请求
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # 更新前端静态文件路径
    frontend_path = Path(__file__).parent.parent / "frontend/dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True))
    
    # 创建塔罗牌服务实例
    tarot_service = TarotService()
    
    @app.post("/api/reading")
    async def do_reading(question: str, spread_type: str):
        """执行塔罗牌解读"""
        try:
            return tarot_service.do_reading(question, spread_type)
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"解读过程出错: {str(e)}")
            return {"error": "服务器内部错误"}
    
    return app

def main():
    """运行应用"""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    sys.exit(main()) 