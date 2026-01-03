import ccxt.async_support as ccxt
from fastapi import FastAPI, HTTPException
import os
import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(title="Exchange Adapter Service", version="1.0.0")

# AuthService URL (내부 도커 네트워크)
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
            'adjustForTimeDifference': True, # 서버 시간과 로컬 시간 동기화 유지
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

    # 2. 거래소 연결
    exchange_id = creds['exchange']
    
    # 디버그: 외부 IP 확인 (API 화이트리스트 검증용)
    try:
        async with httpx.AsyncClient() as ip_client:
            ip_resp = await ip_client.get('https://api.ipify.org')
            print(f"[INFO] Current Execution IP: {ip_resp.text}")
    except Exception as ip_err:
        print(f"[WARN] Failed to check IP: {ip_err}")

    print(f"[INFO] Connecting to {exchange_id} for key {key_id}...")
    
    exchange = await get_exchange_client(exchange_id, creds['publicKey'], creds['secretKey'])
    
    try:
        # 3. 연결 및 시간 동기화 확인
        # load_markets()가 'adjustForTimeDifference' 옵션을 통해 시간 동기화를 수행함
        await exchange.load_markets() 
        print(f"[정보] {exchange_id} 연결 성공. 시간 동기화 완료.")

        # 4. 잔고 조회
        print(f"[INFO] Fetching balance for key {key_id}...")
        balance = await exchange.fetch_balance()
        #print(f"[DEBUG] Raw Balance for key {key_id}: {balance}")
        
        # 5. Normalize & Calculate Value
        assets = []
        total_usdt = 0.0
        
        if 'total' in balance:
            # 먼저, 0보다 큰 자산만 식별
            non_zero_assets = {
                curr: amt for curr, amt in balance['total'].items() 
                if amt > 0
            }

            # 현재가를 조회할 심볼 목록 준비 (예: BTC/USDT)
            # 기축 통화(Quote Currency)는 USDT로 가정
            symbols_to_fetch = []
            for currency in non_zero_assets.keys():
                if currency != 'USDT':
                    # 마켓이 존재하는지 확인 (소규모 코인은 USDT 페어가 없을 수 있음)
                    # 일반적인 페어 형식을 시도
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

@app.get("/market/depth")
async def get_depth(key_id: str, symbol: str, limit: int = 50):
    # 1. 자격 증명 조회 (거래소 라우팅 용도)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/internal/keys/{key_id}/secret")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to retrieve key")
            creds = resp.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    exchange_id = creds["exchange"]
    exchange = await get_exchange_client(exchange_id, creds["publicKey"], creds["secretKey"])

    try:
        await exchange.load_markets()
        ob = await exchange.fetch_order_book(symbol, limit=limit)
        bids = ob.get("bids") or []
        asks = ob.get("asks") or []

        best_bid = float(bids[0][0]) if bids else None
        best_ask = float(asks[0][0]) if asks else None

        return {
            "symbol": symbol,
            "timestamp": ob.get("timestamp"),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bids": bids,
            "asks": asks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await exchange.close()


@app.get("/market/trades")
async def get_trades(key_id: str, symbol: str, limit: int = 100) -> Dict[str, Any]:
    # 1. 자격 증명 조회 (거래소 라우팅 용도)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{AUTH_SERVICE_URL}/internal/keys/{key_id}/secret")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to retrieve key")
            creds = resp.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    exchange_id = creds["exchange"]
    exchange = await get_exchange_client(exchange_id, creds["publicKey"], creds["secretKey"])

    try:
        await exchange.load_markets()
        trades = await exchange.fetch_trades(symbol, limit=limit)

        normalized = []
        for t in trades or []:
            side = t.get("side")
            if side is not None:
                side = side.lower()
            normalized.append(
                {
                    "timestamp": t.get("timestamp"),
                    "price": t.get("price"),
                    "amount": t.get("amount"),
                    "side": side,
                }
            )

        return {"symbol": symbol, "trades": normalized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await exchange.close()

@app.get("/market/ticker")
async def get_ticker(key_id: str, symbol: str):    # 거래소 컨텍스트를 파악하기 위해 key_id 필요
    # 1. 자격 증명 조회 (주로 거래소 라우팅 용도)
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
        # 마켓 정보를 로드하여 제약조건(Limits) 확인
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker(symbol)
        
        # 제약조건(Limits) 추출
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
        # 2. 주문 실행
        print(f"[정보] {order.symbol} {order.side} 주문 실행 (수량: {order.amount})")
        # CCXT create_order 시그니처: (symbol, type, side, amount, price=None, params={})
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
