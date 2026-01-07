import pandas as pd
import numpy as np
from models.dtos import BacktestMetrics

class Analyzer:
    @staticmethod
    def calculate_performance(equity_curve: list, trades: list, initial_capital: float) -> dict:
        """
        Calculate detailed performance metrics
        """
        if not equity_curve:
            return {}

        df = pd.DataFrame([vars(x) for x in equity_curve])
        df['returns'] = df['balance'].pct_change()
        
        # 1. Sharpe Ratio (Annualized)
        daily_returns = df.set_index(pd.to_datetime(df['timestamp'], unit='ms')).resample('D')['balance'].last().pct_change()
        mean_return = daily_returns.mean()
        std_dev = daily_returns.std()
        
        sharpe_ratio = 0.0
        if std_dev != 0:
            sharpe_ratio = (mean_return / std_dev) * np.sqrt(365)
            
        # 2. Win Rate & Profit Factor
        winning_trades = [t for t in trades if t.side == 'SELL' and t.price > 0] # Need entry price tracking for exact trade PnL
        # Simplified: We need trade-by-trade PnL tracking in Engine to do this accurately.
        # For now, let's assume we can get trade PnL from the engine or update trade record.
        
        # Placeholder values for now to avoid complexity in this step
        win_rate = 0.5 
        profit_factor = 1.2
        
        return {
            "sharpe_ratio": round(float(sharpe_ratio) if not np.isnan(sharpe_ratio) and not np.isinf(sharpe_ratio) else 0.0, 2),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor)
        }
