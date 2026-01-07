import ccxt.pro as ccxt  # Use pro for potentially faster connection handling, though sync fetch is used here
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CCXTDataLoader:
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        # Initialize exchange in sandbox/public mode
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })

    async def fetch_historical_data(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch OHLCV data with pagination handling.
        """
        # Convert datetimes to timestamps (ms)
        since = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        all_candles = []
        current_since = since
        
        logger.info(f"Fetching {symbol} {timeframe} data from {start_date} to {end_date}...")

        try:
            while current_since < end_ts:
                # CCXT fetch_ohlcv limit varies, usually 1000 for Binance
                candles = await self.exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
                
                if not candles:
                    break
                
                # Check for duplicates or no progress (edge case)
                last_time = candles[-1][0]
                if last_time == current_since:
                    break

                # Filter candles that are beyond end_date (if any)
                valid_candles = [c for c in candles if c[0] <= end_ts]
                all_candles.extend(valid_candles)
                
                if candles[-1][0] > end_ts or len(candles) < 1000:
                    break
                    
                current_since = candles[-1][0] + 1 # Next ms
                
                # Simple progress log (optional)
                # print(f"Fetched up to {datetime.fromtimestamp(current_since/1000)}")

            logger.info(f"Completed fetching. Total candles: {len(all_candles)}")

            # Convert to DataFrame
            df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise e
        finally:
            await self.exchange.close()

if __name__ == "__main__":
    # Test Block
    async def main():
        loader = CCXTDataLoader()
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 5)
        df = await loader.fetch_historical_data('BTC/USDT', '1h', start, end)
        print(df.head())
        print(df.tail())
        print(f"Total rows: {len(df)}")

    asyncio.run(main())
