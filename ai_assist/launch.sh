#!/bin/bash
export MCP_API_KEY="your-secure-api-key"
export MCP_PROJECT_PATH="/workspace/sportsipy/sportsipy"
export MCP_PORT=5000

uvicorn server:app --host 0.0.0.0 --port 5000
