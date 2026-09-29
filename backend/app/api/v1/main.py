from fastapi import APIRouter
router = APIRouter()

@router.get("/api/hello")
def get_main_data():
    return {
        "message": "Hello from FastAPI!",
        "status": "success",
        "user_count": 10
    }