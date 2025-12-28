import ccxt.async_support as ccxt
from fastapi import FastAPI, HTTPException
import os
import httpx
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Exchange Adapter Service", version="1.0.0")

# AuthService URL (Internal Docker Network)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

class AssetBalance(BaseModel):
    asset: str
    free: float
    locked: float
    usdtValue: float

class AccountBalance(BaseModel):
    totalUsdtValue: float
    assets: List[AssetBalance]

async def get_exchange_client(exchange_id: str, api_key: str, secret: str):
    # Initialize CCXT exchange class instance (Async)
    if not hasattr(ccxt, exchange_id):
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange_id}")
    
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'adjustForTimeDifference': True, # Keep local time synced with server time
            'defaultType': 'spot' 
        }
    })
    return exchange

@app.get("/balance/{key_id}", response_model=AccountBalance)
async def get_balance(key_id: str):
    # 1. Get Credentials from AuthService
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/internal/keys/{key_id}/secret")
            if resp.status_code != 200:
                print(f"[ERROR] AuthService returned {resp.status_code}: {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail="Failed to retrieve key from AuthService")
            creds = resp.json()
            print(f"[INFO] Retrieved credentials for key {key_id} from AuthService.")
            print(f"[DEBUG] Using Public Key: {creds.get('publicKey', 'N/A')}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"AuthService unavailable: {exc}")

    # 2. Connect to Exchange
    exchange_id = creds['exchange']
    
    # Debug: Check External IP
    try:
        async with httpx.AsyncClient() as ip_client:
            ip_resp = await ip_client.get('https://api.ipify.org')
            print(f"[INFO] Current Execution IP: {ip_resp.text}")
    except Exception as ip_err:
        print(f"[WARN] Failed to check IP: {ip_err}")

    print(f"[INFO] Connecting to {exchange_id} for key {key_id}...")
    
    exchange = await get_exchange_client(exchange_id, creds['publicKey'], creds['secretKey'])
    
    try:
        # 3. Connection & Time Sync Check
        # load_markets() will sync time via 'adjustForTimeDifference'
        await exchange.load_markets() 
        print(f"[INFO] Successfully connected to {exchange_id}. Time sync complete.")

        # 4. Fetch Balance
        print(f"[INFO] Fetching balance for key {key_id}...")
        balance = await exchange.fetch_balance()
        #print(f"[DEBUG] Raw Balance for key {key_id}: {balance}")
        
        # 5. Normalize & Calculate Value
        assets = []
        total_usdt = 0.0
        
        if 'total' in balance:
            # First, identify all non-zero assets
            non_zero_assets = {
                curr: amt for curr, amt in balance['total'].items() 
                if amt > 0
            }

            # Prepare list of symbols to fetch prices for (e.g. BTC/USDT)
            # We assume USDT is the quote currency.
            symbols_to_fetch = []
            for currency in non_zero_assets.keys():
                if currency != 'USDT':
                    # Check if market exists (some small assets might not have USDT pair)
                    # We try common pair formats.
                    symbol = f"{currency}/USDT"
                    if symbol in exchange.markets:
                        symbols_to_fetch.append(symbol)

            ticker_prices = {}
            if symbols_to_fetch:
                try:
                    print(f"[INFO] Fetching tickers for: {symbols_to_fetch}")
                    tickers = await exchange.fetch_tickers(symbols_to_fetch)
                    for symbol, ticker in tickers.items():
                        # Extract base currency from symbol (e.g. BTC from BTC/USDT)
                        base_currency = symbol.split('/')[0]
                        if ticker and 'last' in ticker:
                            ticker_prices[base_currency] = ticker['last']
                except Exception as ticker_err:
                    print(f"[WARN] Failed to fetch tickers: {ticker_err}")

            # Calculate values
            for currency, amount in non_zero_assets.items():
                free = balance['free'].get(currency, 0)
                locked = balance['used'].get(currency, 0)
                
                val = 0.0
                if currency == 'USDT':
                    val = amount
                elif currency in ticker_prices:
                    price = ticker_prices[currency]
                    val = amount * price
                
                # Only add to total if we successfully calculated a value (or it's USDT)
                total_usdt += val

                assets.append(AssetBalance(
                    asset=currency,
                    free=free,
                    locked=locked,
                    usdtValue=val 
                ))
        
        return AccountBalance(totalUsdtValue=total_usdt, assets=assets)

        return AccountBalance(totalUsdtValue=total_usdt, assets=assets)

    except Exception as e:
        import datetime
        print(f"[ERROR] Time: {datetime.datetime.now()} | Exchange Error: {exchange_id} {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup async session
        if exchange:
            await exchange.close()

class OrderRequest(BaseModel):
    key_id: str
    symbol: str
    side: str # 'buy' or 'sell'
    amount: float
    order_type: str = 'market'
    price: Optional[float] = None

@app.get("/market/ticker")
async def get_ticker(key_id: str, symbol: str):    # Require key_id to determine exchange context
    # 1. Get Credentials (for exchange routing, mostly)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/internal/keys/{key_id}/secret")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to retrieve key")
            creds = resp.json()
        except Exception as e:
             raise HTTPException(status_code=503, detail=str(e))

    exchange_id = creds['exchange']
    exchange = await get_exchange_client(exchange_id, creds['publicKey'], creds['secretKey'])
    
    try:
        # Load markets to get limits
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker(symbol)
        
        # Extract Limits
        market = exchange.market(symbol)
        min_notional = market.get('limits', {}).get('cost', {}).get('min')
        min_amount = market.get('limits', {}).get('amount', {}).get('min')

        return {
            "symbol": symbol, 
            "price": ticker['last'],
            "limits": {
                "min_notional": min_notional,
                "min_amount": min_amount
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await exchange.close()

@app.post("/order")
async def place_order(order: OrderRequest):
    # 1. Get Credentials
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/internal/keys/{order.key_id}/secret")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to retrieve key")
            creds = resp.json()
        except Exception as e:
             raise HTTPException(status_code=503, detail=str(e))

    exchange_id = creds['exchange']
    exchange = await get_exchange_client(exchange_id, creds['publicKey'], creds['secretKey'])

    try:
        # 2. Place Order
        print(f"[INFO] Placing {order.side} order for {order.symbol} amount={order.amount}")
        # CCXT create_order signature: (symbol, type, side, amount, price=None, params={})
        result = await exchange.create_order(
            symbol=order.symbol,
            type=order.order_type,
            side=order.side,
            amount=order.amount,
            price=order.price
        )
        return {"status": "filled", "order_id": result['id'], "details": result}
    except Exception as e:
        print(f"[ERROR] Order Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await exchange.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "exchange-adapter"}
