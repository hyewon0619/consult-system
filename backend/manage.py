from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.common.utils import register 

def create_app():
    app = FastAPI(title="Consult Support API")

    import os
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=origins,    
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register(app, 'app.api.v1.main')
    register(app, 'app.api.v1.model')
    
    return app


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("manage:create_app", host="0.0.0.0", port=8000, reload=True, factory=True)