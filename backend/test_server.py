from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/test")
def test_endpoint():
    return {"status": "ok", "message": "Test endpoint working"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 