from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.documents import router as document_router
from app.api.query import router as query_router

app = FastAPI(
    title="Project Atlas",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    # Required for the session cookie to be sent on cross-origin requests
    # from the frontend. Note this is why allow_origins cannot be "*" -
    # browsers reject the wildcard when credentials are enabled.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(document_router)
app.include_router(query_router)


@app.get("/")
async def root():
    return {"message": "Project Atlas API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}