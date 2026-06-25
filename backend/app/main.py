from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # auto-find .env, searches up from cwd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import OUTPUT_DIR
from app.routers import generate, plan, providers, upload

app = FastAPI(title="Ecom Kit Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(plan.router)
app.include_router(providers.router)
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
