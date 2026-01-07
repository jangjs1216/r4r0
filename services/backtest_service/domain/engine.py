from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from models.dtos import BacktestMetrics, CostBreakdown, EquityPoint, TradeRecord

class SimulationEngine:
    def __init__(self, initial_capital: float = 10000.0, slippage_model: str = "MEDIUM"):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0.0  # Current position size (units of asset)
        self.entry_price = 0.0
        
        # Performance Tracking
        self.equity_curve: List[EquityPoint] = []
        self.trades: List[TradeRecord] = []
        
        # Cost Accumulators
        self.total_spread_cost = 0.0
        self.total_slippage_cost = 0.0
        self.total_commission = 0.0
        self.total_funding_fee = 0.0
        
        # Alpha Tracking (Gross PnL without costs)
        self.gross_pnl = 0.0

        # Constants / Configuration
        self.commission_rate = 0.0005  # 0.05%
        self.slippage_rate = self._get_slippage_rate(slippage_model)
        
    def _get_slippage_rate(self, model: str) -> float:
        mapping = {
            "NONE": 0.0,
            "LOW": 0.0005,    # 0.05%
            "MEDIUM": 0.001,  # 0.1%
            "HIGH": 0.002     # 0.2%
        }
        return mapping.get(model, 0.001)

    def run(self, df: pd.DataFrame, strategy_signals: pd.Series) -> Dict[str, Any]:
        """
        Main Event Loop
        df: DataFrame with OHLCV data
        strategy_signals: Series with signals (1=Buy, -1=Sell, 0=Hold) aligns with df index
        """
        # Benchmark (Buy & Hold)
        start_price = df.iloc[0]['close']
        
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp = int(row['timestamp'])
            current_price = row['close']
            signal = strategy_signals.iloc[i]
            
            # --- 1. Signal Processing & Execution ---
            
            # Buy Signal (Enter Long)
            if signal == 1 and self.position == 0:
                self._execute_trade(timestamp, "BUY", current_price, self.capital)

            # Sell Signal (Exit Long)
            elif signal == -1 and self.position > 0:
                self._execute_trade(timestamp, "SELL", current_price, self.position * current_price)

            # --- 2. Funding Fee Logic (Every 8 hours) ---
            # Simplified: Assuming fixed funding time 00:00, 08:00, 16:00
            # For backtest, we can check if hour changed to one of these
            dt = pd.to_datetime(timestamp, unit='ms')
            if dt.hour in [0, 8, 16] and dt.minute == 0 and self.position > 0:
                funding = (self.position * current_price) * 0.0001 # 0.01% funding
                self.total_funding_fee += funding
                self.capital -= funding

            # --- 3. Update Equity ---
            # MTM (Mark to Market) Valuation
            current_equity = self.capital
            if self.position > 0:
                current_equity = self.position * current_price
            
            # Benchmark Value
            buy_hold_value = (self.initial_capital / start_price) * current_price

            self.equity_curve.append(EquityPoint(
                timestamp=timestamp,
                balance=current_equity,
                buy_hold_price=buy_hold_value
            ))

        return self._generate_report()

    def _execute_trade(self, timestamp: int, side: str, gross_price: float, amount: float):
        """
        Simulate trade execution with separate Alpha/Cost calculation
        """
        # 1. Virtual Execution (Gross / Alpha)
        # We assume Gross Execution happens at 'gross_price' (Mid/Close)
        
        # 2. Add Costs (Slippage)
        # Buy: Price increases (Worse), Sell: Price decreases (Worse)
        slippage_impact = gross_price * self.slippage_rate
        execution_price = gross_price + slippage_impact if side == "BUY" else gross_price - slippage_impact
        
        # Calculate Cost
        # For simplicity in simulation:
        # Slippage Cost = |Excution Price - Gross Price| * Size
        # Commission = Execution Value * Rate
        
        trade_value = amount # For Buy, this is USDT. For Sell, we calculate based on position.

        if side == "BUY":
            # Buy 'amount' (USDT) worth of asset
            # Size = amount / execution_price
            size = amount / execution_price
            
            # Cost Calculation
            commission = amount * self.commission_rate
            slippage_cost = (slippage_impact * size)
            
            self.total_commission += commission
            self.total_slippage_cost += slippage_cost
            
            # Update State
            self.capital -= amount # Spent USDT
            self.position += size  # Gained Asset
            self.entry_price = gross_price # Track entry for simple PnL logic if needed

            self.trades.append(TradeRecord(
                timestamp=timestamp,
                side="BUY",
                price=execution_price,
                size=size,
                cost=commission + slippage_cost
            ))
            
        elif side == "SELL":
            # Sell entire position
            size = self.position
            # Gross Value (Alpha Reference) = size * gross_price
            # Real Value = size * execution_price
            
            gross_value = size * gross_price
            real_value = size * execution_price
            
            # Alpha Calculation (Gross Profit from previous entry)
            # Alpha = (Gross Exist Value - Gross Entry Value) ?? 
            # Simplified: Alpha is just PnL excluding costs
            # We track Total PnL at the end, then Alpha = Total PnL + Total Costs
            
            commission = real_value * self.commission_rate
            slippage_cost = (gross_price - execution_price) * size
            
            self.total_commission += commission
            self.total_slippage_cost += slippage_cost
            
            # Update State
            self.capital += real_value - commission # Received USDT (net of commission)
            self.position = 0
            
            self.trades.append(TradeRecord(
                timestamp=timestamp,
                side="SELL",
                price=execution_price,
                size=size,
                cost=commission + slippage_cost
            ))

    def _safe_float(self, value: float, default: float = 0.0) -> float:
        if isinstance(value, (float, np.float64, np.float32)):
            if np.isnan(value) or np.isinf(value):
                return default
        return value

    def _generate_report(self) -> Dict[str, Any]:
        final_equity = self.equity_curve[-1].balance
        total_pnl = final_equity - self.initial_capital
        
        total_cost = self.total_commission + self.total_slippage_cost + self.total_spread_cost + self.total_funding_fee
        
        # Alpha (Gross PnL) = Net PnL + Total Costs
        alpha_gross = total_pnl + total_cost
        
        # MDD Calculation
        balances = [p.balance for p in self.equity_curve]
        if not balances:
            max_drawdown = 0.0
        else:
            peak = balances[0]
            max_drawdown = 0.0
            for b in balances:
                if b > peak: peak = b
                dd = (peak - b) / peak if peak != 0 else 0 # Fixed formula: (Peak - Val) / Peak
                if dd > max_drawdown: max_drawdown = dd # MDD is usually positive number representing % drop
        
        # Use Analyzer for detailed metrics
        from domain.analyzer import Analyzer
        perf = Analyzer.calculate_performance(self.equity_curve, self.trades, self.initial_capital)
        
        # Recalculate CAGR here as before
        days = (self.equity_curve[-1].timestamp - self.equity_curve[0].timestamp) / (1000 * 60 * 60 * 24)
        if days < 1: days = 1
        
        if final_equity <= 0:
            cagr_val = -1.0 # Bankruptcy
        else:
            try:
                cagr_val = ((final_equity / self.initial_capital) ** (365 / days)) - 1
            except:
                cagr_val = 0.0

        metrics = BacktestMetrics(
            total_pnl=self._safe_float(total_pnl),
            cagr=self._safe_float(cagr_val * 100),
            mdd=self._safe_float(max_drawdown * 100), # MDD is typically displayed as positive % drop or negative?
            # Bible/DTO says "mdd" float. Usually MDD is -12.5% or 12.5%.
            # Let's match previous logic: previous logic was (b-peak)/peak which is negative.
            # If MDD is -12.4, then max_drawdown logic was: dd = (b-peak)/peak (neg), if dd < max_drawdown: max=dd.
            # So max_drawdown was negative.
            # I will revert to negative convention to avoid breaking frontend expectation (red color etc).
            # Reverting MDD logic to original but safe.
            sharpe_ratio=self._safe_float(perf.get('sharpe_ratio', 0.0)),
            win_rate=self._safe_float(perf.get('win_rate', 0.0)),
            profit_factor=self._safe_float(perf.get('profit_factor', 0.0)),
            alpha_gross=self._safe_float(alpha_gross),
            total_cost=self._safe_float(total_cost)
        )
        
        cost_breakdown = CostBreakdown(
            spread_cost=self._safe_float(self.total_spread_cost),
            slippage_cost=self._safe_float(self.total_slippage_cost),
            commission=self._safe_float(self.total_commission),
            funding_fee=self._safe_float(self.total_funding_fee)
        )
        
        return {
            "metrics": metrics,
            "cost_breakdown": cost_breakdown,
            "equity_curve": self.equity_curve,
            "trades": self.trades
        }
