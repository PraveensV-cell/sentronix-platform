from fastapi import FastAPI

app = FastAPI(
    title="SENTRONIX API Gateway", version="0.1.0", docs_url="/docs", redoc_url="/redoc"
)


@app.get("/")
async def root():
    return {"application": "SENTRONIX", "service": "API Gateway", "status": "Running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
