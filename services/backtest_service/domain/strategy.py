from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from the dataframe.
        Returns a Series where 1=Buy, -1=Sell, 0=Hold.
        """
        pass

class SmaStrategy(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Avoid SettingWithCopyWarning
        df = df.copy()
        
        df['short_ma'] = df['close'].rolling(window=self.short_window).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[df['short_ma'] > df['long_ma']] = 1  # Buy condition
        signals[df['short_ma'] < df['long_ma']] = -1 # Sell condition
        
        # Keep signal only on change (Crossover)
        signals = signals.diff().fillna(0)
        signals = signals.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        
        return signals

class RsiStrategy(Strategy):
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Avoid SettingWithCopyWarning
        df = df.copy()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        # Use Wilders Smoothing or Simple Moving Average? 
        # For simplicity in this demo, using Simple Moving Average (SMA)
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()

        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=df.index)
        
        # Buy Signal (Oversold -> Cross above 30?) OR just < 30 (State)
        # Usually strategy is: Buy when crossing UP 30, Sell when crossing DOWN 70.
        # Let's do state-based for simplicity: 
        # If RSI < 30 -> Buy (1)
        # If RSI > 70 -> Sell (-1)
        # Hold otherwise.
        # But engine executes on state "change" better if we return 1.
        # Actually Engine checks: if signal==1 and pos==0 -> BUY.
        # So we can output 1 as long as condition holds or just once.
        # Let's output state 1 while condition holds.
        
        signals[df['rsi'] < self.oversold] = 1
        signals[df['rsi'] > self.overbought] = -1
        
        # Debounce: only trigger on change to avoid redundant signals if engine handles it,
        # but Engine checks `if signal == 1 and self.position == 0`.
        # So continuous 1s are fine, engine just ignores subsequent ones.
        return signals

class StrategyFactory:
    @staticmethod
    def create_strategy(bot_config: Dict[str, Any]) -> Strategy:
        pipeline_config = bot_config.get('pipeline', {})
        
        # Determine strategy type
        raw_strategy = pipeline_config.get('type') or pipeline_config.get('strategy')
        
        if isinstance(raw_strategy, dict):
            # If it's a node object, look for 'type' or 'subtype'
            strategy_type = raw_strategy.get('subtype', raw_strategy.get('type', 'SMA'))
        elif isinstance(raw_strategy, str):
            strategy_type = raw_strategy
        else:
            strategy_type = 'SMA'

        strategy_type = strategy_type.upper()
        
        if strategy_type == 'SMA':
            short_window = int(pipeline_config.get('short_window', 20))
            long_window = int(pipeline_config.get('long_window', 50))
            return SmaStrategy(short_window=short_window, long_window=long_window)
        
        if strategy_type == 'RSI':
            period = int(pipeline_config.get('period', 14))
            return RsiStrategy(period=period)

        # Default fallback
        return SmaStrategy()
