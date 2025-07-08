from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/test", tags=["測試"])


@router.get("/")
async def get_test_message():
    return {"message": "Test router is working!"}
