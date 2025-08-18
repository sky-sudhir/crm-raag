import uvicorn

from api.config import PORT


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="127.0.0.1", port=PORT, reload=True)