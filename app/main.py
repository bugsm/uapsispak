"""Main Application - Sistem Pakar Defisiensi Unsur Hara Tomat"""

import os
import sys
import logging
import time
from typing import Callable

# Fix import path - bisa dijalankan dari app/ atau root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import web
from app.services.knowledge_base import KnowledgeBaseError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sistem Pakar Defisiensi Unsur Hara Tomat",
    description=(
        "Aplikasi web Sistem Pakar untuk mendiagnosa kekurangan unsur hara "
        "pada tanaman tomat menggunakan metode Certainty Factor (CF). "
        "Sistem ini membantu petani mengidentifikasi defisiensi nutrisi "
        "seperti Nitrogen, Fosfor, Kalium, Kalsium, Magnesium, dan Boron."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")


# ==================== Middleware ====================

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Logging middleware untuk setiap request"""
    start_time = time.time()
    
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Response: {request.method} {request.url.path} Status: {response.status_code} Time: {process_time:.3f}s")
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error processing {request.method} {request.url.path}: {str(e)} "
            f"(Time: {process_time:.3f}s)",
            exc_info=True
        )
        raise


# ==================== Error Handlers ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler untuk HTTP exceptions"""
    logger.warning(
        f"HTTP {exc.status_code} error: {exc.detail} "
        f"for {request.method} {request.url.path}"
    )
    
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error {exc.status_code}</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>Error {exc.status_code}</h1>
                    <p>{exc.detail}</p>
                    <a href="/">Kembali ke Halaman Utama</a>
                </body>
            </html>
            """,
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler untuk validation errors"""
    logger.warning(
        f"Validation error for {request.method} {request.url.path}: {exc.errors()}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(KnowledgeBaseError)
async def knowledge_base_error_handler(request: Request, exc: KnowledgeBaseError):
    """Handler untuk knowledge base errors"""
    logger.error(f"Knowledge base error: {str(exc)}", exc_info=True)
    
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            content="""
            <html>
                <head><title>System Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>System Error</h1>
                    <p>Terjadi error pada knowledge base. Silakan hubungi administrator.</p>
                    <a href="/">Kembali ke Halaman Utama</a>
                </body>
            </html>
            """,
            status_code=500
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Knowledge base error",
            "detail": str(exc),
            "status_code": 500
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler untuk unhandled exceptions"""
    logger.error(
        f"Unhandled exception for {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            content="""
            <html>
                <head><title>Internal Server Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>Internal Server Error</h1>
                    <p>Terjadi error yang tidak terduga. Silakan coba lagi nanti.</p>
                    <a href="/">Kembali ke Halaman Utama</a>
                </body>
            </html>
            """,
            status_code=500
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "status_code": 500
        }
    )


# ==================== Routes ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.services.knowledge_base import load_knowledge_base
        kb = load_knowledge_base(use_cache=True)
        
        return JSONResponse(content={
            "status": "healthy",
            "version": "2.0.0",
            "knowledge_base": {
                "symptoms_count": len(kb.get("symptoms", [])),
                "nutrients_count": len(kb.get("nutrients", [])),
                "rules_count": len(kb.get("rules", []))
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include routers
app.include_router(web.router)


# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Startup event - validasi knowledge base"""
    logger.info("=" * 60)
    logger.info("Starting Sistem Pakar Defisiensi Unsur Hara Tomat")
    logger.info("=" * 60)
    
    try:
        from app.services.knowledge_base import load_knowledge_base
        kb = load_knowledge_base(use_cache=False)
        
        logger.info(f"Knowledge base loaded successfully:")
        logger.info(f"  - Symptoms: {len(kb.get('symptoms', []))}")
        logger.info(f"  - Nutrients: {len(kb.get('nutrients', []))}")
        logger.info(f"  - Rules: {len(kb.get('rules', []))}")
        
    except Exception as e:
        logger.error(f"Error validating knowledge base on startup: {str(e)}")
        logger.warning("Application will continue, but some features may not work")
    
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down application...")


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
