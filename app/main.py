import os
import sys

# Fix import path - bisa dijalankan dari app/ atau root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import web

app = FastAPI(
    title="Sistem Pakar Tomat",
    description="Hybrid Expert System for Tomato Nutrient Deficiency",
    version="1.0.0"
)

# Mount static files
# Ensure the directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
