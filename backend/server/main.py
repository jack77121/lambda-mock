from contextlib import asynccontextmanager
from typing import Union
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from shared.schemas.base_model import ApiResponseBase
from shared.models import Reqs, Ans
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)  # Simple connection test
        print("Database connection established")
    except Exception as e:
        print(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    await engine.dispose()
    print("Database connection closed")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/test")
def test():
    return JSONResponse(
        status_code=422,
        content=ApiResponseBase(
            status="fail", message="test", data=None
        ).model_dump(),
    )


@app.get("/reqs")
async def get_requests(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Reqs))
        requests = result.scalars().all()
        return {"requests": [{"req_uuid": str(req.req_uuid), "input_params": req.input_params, "created_at": req.created_at} for req in requests]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reqs/{req_uuid}")
async def get_request(req_uuid: UUID, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Reqs).where(Reqs.req_uuid == req_uuid))
        request = result.scalar_one_or_none()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return {"req_uuid": str(request.req_uuid), "input_params": request.input_params, "created_at": request.created_at}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ans/{req_uuid}")
async def get_answers(req_uuid: UUID, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Ans).where(Ans.req_uuid == req_uuid))
        answers = result.scalars().all()
        return {"answers": [{"ans_uuid": str(ans.ans_uuid), "output_result": ans.output_result} for ans in answers]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
