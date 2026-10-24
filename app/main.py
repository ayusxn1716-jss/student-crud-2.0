from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import ai, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create the table on first run
    yield


app = FastAPI(
    title="Students Database CRUD API",
    description="EWB Internship project: FastAPI + SQLite, with an optional Ollama AI extension.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(students.router)
app.include_router(ai.router)


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    """The web dashboard."""
    return FileResponse(STATIC_DIR / "index.html")
