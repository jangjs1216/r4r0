from datetime import datetime
import uuid
import logging
from typing import Dict, Any

from models.dtos import RunBacktestRequest, BacktestResponse
from infra.data_loader import CCXTDataLoader
from domain.engine import SimulationEngine
from domain.strategy import StrategyFactory

logger = logging.getLogger(__name__)

class BacktestWorkflowService:
    def __init__(self):
        # In a real app, these might be injected
        self.data_loader = CCXTDataLoader()

    async def run_backtest(self, request: RunBacktestRequest) -> BacktestResponse:
        job_id = str(uuid.uuid4())
        logger.info(f"Starting backtest job {job_id} for bot: {request.bot_config.get('name')}")

        try:
            # 1. Prepare Data
            symbol = request.bot_config.get('global_settings', {}).get('symbol', 'BTC/USDT')
            # Default to 1h if not specified
            timeframe = '1h' 
            
            logger.info(f"Fetching data for {symbol}...")
            df = await self.data_loader.fetch_historical_data(
                symbol, 
                timeframe, 
                request.time_range.start_date, 
                request.time_range.end_date
            )
            
            if df.empty:
                raise ValueError("No data found for the specified range")

            # 2. Strategy Execution
            strategy = StrategyFactory.create_strategy(request.bot_config)
            signals = strategy.generate_signals(df)

            # 3. Simulation
            logger.info("Running simulation...")
            engine = SimulationEngine(
                initial_capital=request.initial_capital,
                slippage_model=request.slippage_model
            )
            
            # Engine now handles everything including calling Analyzer locally or we explicitly call it
            # To keep minimal changes, we assume Engine.run returns the expected dict structure
            # but we will ensure Engine uses Analyzer internally.
            result = engine.run(df, signals)
            
            # 4. Construct Response
            return BacktestResponse(
                job_id=job_id,
                status="COMPLETED",
                metrics=result['metrics'],
                cost_breakdown=result['cost_breakdown'],
                equity_curve=result['equity_curve'],
                trades=result['trades']
            )

        except Exception as e:
            logger.error(f"Backtest job {job_id} failed: {str(e)}")
            # For now, valid response with FAILED status could be better, 
            # but DTO says status is COMPLETED/FAILED.
            # If we raise, FastAPI handles it. 
            # Let's return FAILED response if possible, or just re-raise.
            # Returning FAILED response requires partial data which we don't have.
            # So re-raising is safer for now.
            raise e
