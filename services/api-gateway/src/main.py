from fastapi import FastAPI

app = FastAPI(
    title="SENTRONIX API Gateway",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"application": "SENTRONIX", "service": "API Gateway", "status": "Running"}
