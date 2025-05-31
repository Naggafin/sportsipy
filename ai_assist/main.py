import os
import logging
from pathlib import Path
from .search_engine import index_project_incremental

# MCP-compliant logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get project path from environment (MCP standard)
BASE_DIR = Path(os.getenv("MCP_PROJECT_PATH", os.getcwd()))

if __name__ == "__main__":
    logger.info(f"Starting indexing for project at {BASE_DIR}")
    try:
        index_project_incremental(BASE_DIR)
        logger.info("Project indexed successfully.")
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise