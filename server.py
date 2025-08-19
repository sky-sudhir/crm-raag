import uvicorn

from api.config import PORT


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=PORT, reload=True)