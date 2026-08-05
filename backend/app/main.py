from fastapi import FastAPI

from app.api.documents import router as document_router

app = FastAPI(
    title="Project Atlas",
    version="0.1.0",
)

app.include_router(document_router)


@app.get("/")
async def root():
    return {"message": "Project Atlas API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}