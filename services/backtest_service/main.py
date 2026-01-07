from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models.dtos import RunBacktestRequest, BacktestResponse
from services.workflow_service import BacktestWorkflowService
import logging

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backtest Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection for Service
def get_workflow_service():
    return BacktestWorkflowService()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "backtest-service"}

@app.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: RunBacktestRequest,
    service: BacktestWorkflowService = Depends(get_workflow_service)
):
    logger.info(f"Received backtest request for bot: {request.bot_config.get('name')}")
    try:
        return await service.run_backtest(request)
    except ValueError as e:
        logger.warning(f"Bad Request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
