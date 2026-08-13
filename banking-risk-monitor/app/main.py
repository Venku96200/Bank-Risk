from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .routers import transactions, alerts, dashboard

app=FastAPI(title="Banking Transaction Risk Monitor")
app.include_router(transactions.router); app.include_router(alerts.router); app.include_router(dashboard.router)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # Keep API startup available if the first local embedding-model download is deferred.
    try:
        from .services.rag_explainer import initialise; initialise()
    except Exception as exc: print(f"RAG index will initialise on first explanation: {exc}")
@app.get("/health")
def health(): return {"status":"ok"}
FRONTEND=Path(__file__).resolve().parents[1]/"frontend"
app.mount("/",StaticFiles(directory=FRONTEND,html=True),name="frontend")
