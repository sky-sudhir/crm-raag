import logging
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.utils.error_class import CustomAppException
from src.utils.response_class import APIResponse, ErrorResponse
from src.db.main import init_db
from src.feature.user.routes import user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("server is starting")
    await init_db()
    yield
    print("server is stopped")


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
    filename="backend_errors.log",  # Log file path
    filemode="a"  # Append mode
)
    
    

app = FastAPI(title="My API",
 description="My API description", 
 version="0.0.1",
 lifespan=lifespan)


@app.exception_handler(HTTPException)
async def global_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            data=None,
            total_count=0,
            message=exc.detail,
            success=False
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    stack_trace = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            stack=stack_trace,
            message="Interal Server Error",
            success=False
        ).model_dump()
    )




app.include_router(user_router)