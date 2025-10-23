import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

from app.api import router as api_router

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(CUR_DIR, "app", "agents")

app: FastAPI = get_fast_api_app(agents_dir=AGENT_DIR, web=True)

app.title = "learnforge-agent-api"
app.description = "API for interacting with the Agent learnforge"

app.include_router(api_router, prefix="/api")

# Main execution
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
