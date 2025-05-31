from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from .search_engine import search_code_hybrid, index_project_incremental
from .auth import verify_api_key
from .config import settings
from pathlib import Path
import logging

BASE_DIR = Path(settings.project_path)

app = FastAPI(title="MCP Code Search Server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ContextRequest(BaseModel):
    query: str
    max_tokens: int = 8000

class FileRequest(BaseModel):
    path: str

@app.post("/mcp/v1/context", dependencies=[Depends(verify_api_key)])
async def get_context(request: ContextRequest):
    try:
        result = search_code_hybrid(request.query, k=5, max_tokens=request.max_tokens)
        return {
            "content": result["content"],
            "metadata": result["metadata"],
            "tokens": result["tokens"],
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Context fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch context: {e}")

@app.post("/mcp/v1/context/search", dependencies=[Depends(verify_api_key)])
async def search_context(request: ContextRequest):
    try:
        result = search_code_hybrid(request.query, k=5, max_tokens=request.max_tokens)
        return {
            "results": [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(result["content"].split("\n\n") if result["content"] else [], result["metadata"])
            ],
            "tokens": result["tokens"],
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.post("/mcp/v1/context/file", dependencies=[Depends(verify_api_key)])
async def get_file(request: FileRequest):
    try:
        file_path = BASE_DIR / request.path
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = file_path.read_text()
        tokens = count_tokens(content)
        return {
            "content": content,
            "metadata": {"path": request.path, "source": "codebase"},
            "tokens": tokens,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"File fetch failed: {e}")
        raise HTTPException(status_code=404, detail=f"File fetch failed: {e}")

@app.post("/mcp/v1/context/reindex", dependencies=[Depends(verify_api_key)])
async def reindex():
    try:
        index_project_incremental(BASE_DIR)
        return {"status": "reindexed"}
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reindex failed: {e}")