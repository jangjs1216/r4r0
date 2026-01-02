
아래는 차례로, 구매, 판매가 이루어질 때의 JSON 응답 예시입니다.

r4r0-execution-service   | INFO:httpx:HTTP Request: POST http://exchange-adapter:8001/order "HTTP/1.1 200 OK"
r4r0-execution-service   | INFO:execution-service.ledger-adapter:🔍 [RAW EXCHANGE RESPONSE]:
r4r0-execution-service   | {
r4r0-execution-service   |   "status": "filled",
r4r0-execution-service   |   "order_id": "54762105231",
r4r0-execution-service   |   "details": {
r4r0-execution-service   |     "info": {
r4r0-execution-service   |       "symbol": "BTCUSDT",
r4r0-execution-service   |       "orderId": "54762105231",
r4r0-execution-service   |       "orderListId": "-1",
r4r0-execution-service   |       "clientOrderId": "x-R4BD3S8232929ed54f93b91c2a4d2b",
r4r0-execution-service   |       "transactTime": "1767292988078",
r4r0-execution-service   |       "price": "0.00000000",
r4r0-execution-service   |       "origQty": "0.00016000",
r4r0-execution-service   |       "executedQty": "0.00016000",
r4r0-execution-service   |       "origQuoteOrderQty": "0.00000000",
r4r0-execution-service   |       "cummulativeQuoteQty": "14.10593280",
r4r0-execution-service   |       "status": "FILLED",
r4r0-execution-service   |       "timeInForce": "GTC",
r4r0-execution-service   |       "type": "MARKET",
r4r0-execution-service   |       "side": "BUY",
r4r0-execution-service   |       "workingTime": "1767292988078",
r4r0-execution-service   |       "fills": [
r4r0-execution-service   |         {
r4r0-execution-service   |           "price": "88162.08000000",
r4r0-execution-service   |           "qty": "0.00016000",
r4r0-execution-service   |           "commission": "0.00000016",
r4r0-execution-service   |           "commissionAsset": "BTC",
r4r0-execution-service   |           "tradeId": "5724806453"
r4r0-execution-service   |         }
r4r0-execution-service   |       ],
r4r0-execution-service   |       "selfTradePreventionMode": "EXPIRE_MAKER"
r4r0-execution-service   |     },
r4r0-execution-service   |     "id": "54762105231",
r4r0-execution-service   |     "clientOrderId": "x-R4BD3S8232929ed54f93b91c2a4d2b",
r4r0-execution-service   |     "timestamp": 1767292988078,
r4r0-execution-service   |     "datetime": "2026-01-01T18:43:08.078Z",
r4r0-execution-service   |     "lastTradeTimestamp": 1767292988078,
r4r0-execution-service   |     "lastUpdateTimestamp": 1767292988078,
r4r0-execution-service   |     "symbol": "BTC/USDT",
r4r0-execution-service   |     "type": "market",
r4r0-execution-service   |     "timeInForce": "GTC",
r4r0-execution-service   |     "postOnly": false,
r4r0-execution-service   |     "reduceOnly": null,
r4r0-execution-service   |     "side": "buy",
r4r0-execution-service   |     "price": 88162.08,
r4r0-execution-service   |     "triggerPrice": null,
r4r0-execution-service   |     "amount": 0.00016,
r4r0-execution-service   |     "cost": 14.1059328,
r4r0-execution-service   |     "average": 88162.08,
r4r0-execution-service   |     "filled": 0.00016,
r4r0-execution-service   |     "remaining": 0.0,
r4r0-execution-service   |     "status": "closed",
r4r0-execution-service   |     "fee": {
r4r0-execution-service   |       "currency": "BTC",
r4r0-execution-service   |       "cost": 1.6e-07
r4r0-execution-service   |     },
r4r0-execution-service   |     "trades": [
r4r0-execution-service   |       {
r4r0-execution-service   |         "info": {
r4r0-execution-service   |           "price": "88162.08000000",
r4r0-execution-service   |           "qty": "0.00016000",
r4r0-execution-service   |           "commission": "0.00000016",
r4r0-execution-service   |           "commissionAsset": "BTC",
r4r0-execution-service   |           "tradeId": "5724806453"
r4r0-execution-service   |         },
r4r0-execution-service   |         "timestamp": null,
r4r0-execution-service   |         "datetime": null,
r4r0-execution-service   |         "symbol": "BTC/USDT",
r4r0-execution-service   |         "id": "5724806453",
r4r0-execution-service   |         "order": null,
r4r0-execution-service   |         "type": null,
r4r0-execution-service   |         "side": null,
r4r0-execution-service   |         "takerOrMaker": null,
r4r0-execution-service   |         "price": 88162.08,
r4r0-execution-service   |         "amount": 0.00016,
r4r0-execution-service   |         "cost": 14.1059328,
r4r0-execution-service   |         "fee": {
r4r0-execution-service   |           "cost": 1.6e-07,
r4r0-execution-service   |           "currency": "BTC"
r4r0-execution-service   |         },
r4r0-execution-service   |         "fees": [
r4r0-execution-service   |           {
r4r0-execution-service   |             "cost": 1.6e-07,
r4r0-execution-service   |             "currency": "BTC"
r4r0-execution-service   |           }
r4r0-execution-service   |         ]
r4r0-execution-service   |       }
r4r0-execution-service   |     ],
r4r0-execution-service   |     "fees": [
r4r0-execution-service   |       {
r4r0-execution-service   |         "currency": "BTC",
r4r0-execution-service   |         "cost": 1.6e-07
r4r0-execution-service   |       }
r4r0-execution-service   |     ],
r4r0-execution-service   |     "stopPrice": null,
r4r0-execution-service   |     "takeProfitPrice": null,
r4r0-execution-service   |     "stopLossPrice": null
r4r0-execution-service   |   }
r4r0-execution-service   | }

r4r0-execution-service   | INFO:httpx:HTTP Request: POST http://exchange-adapter:8001/order "HTTP/1.1 200 OK"
r4r0-execution-service   | INFO:execution-service.ledger-adapter:🔍 [RAW EXCHANGE RESPONSE]:
r4r0-execution-service   | {
r4r0-execution-service   |   "status": "filled",
r4r0-execution-service   |   "order_id": "54762119973",
r4r0-execution-service   |   "details": {
r4r0-execution-service   |     "info": {
r4r0-execution-service   |       "symbol": "BTCUSDT",
r4r0-execution-service   |       "orderId": "54762119973",
r4r0-execution-service   |       "orderListId": "-1",
r4r0-execution-service   |       "clientOrderId": "x-R4BD3S8228b29a374a977e8c4b1012",
r4r0-execution-service   |       "transactTime": "1767293049327",
r4r0-execution-service   |       "price": "0.00000000",
r4r0-execution-service   |       "origQty": "0.00016000",
r4r0-execution-service   |       "executedQty": "0.00016000",
r4r0-execution-service   |       "origQuoteOrderQty": "0.00000000",
r4r0-execution-service   |       "cummulativeQuoteQty": "14.10804640",
r4r0-execution-service   |       "status": "FILLED",
r4r0-execution-service   |       "timeInForce": "GTC",
r4r0-execution-service   |       "type": "MARKET",
r4r0-execution-service   |       "side": "SELL",
r4r0-execution-service   |       "workingTime": "1767293049327",
r4r0-execution-service   |       "fills": [
r4r0-execution-service   |         {
r4r0-execution-service   |           "price": "88175.29000000",
r4r0-execution-service   |           "qty": "0.00016000",
r4r0-execution-service   |           "commission": "0.01410805",
r4r0-execution-service   |           "commissionAsset": "USDT",
r4r0-execution-service   |           "tradeId": "5724807603"
r4r0-execution-service   |         }
r4r0-execution-service   |       ],
r4r0-execution-service   |       "selfTradePreventionMode": "EXPIRE_MAKER"
r4r0-execution-service   |     },
r4r0-execution-service   |     "id": "54762119973",
r4r0-execution-service   |     "clientOrderId": "x-R4BD3S8228b29a374a977e8c4b1012",
r4r0-execution-service   |     "timestamp": 1767293049327,
r4r0-execution-service   |     "datetime": "2026-01-01T18:44:09.327Z",
r4r0-execution-service   |     "lastTradeTimestamp": 1767293049327,
r4r0-execution-service   |     "lastUpdateTimestamp": 1767293049327,
r4r0-execution-service   |     "symbol": "BTC/USDT",
r4r0-execution-service   |     "type": "market",
r4r0-execution-service   |     "timeInForce": "GTC",
r4r0-execution-service   |     "postOnly": false,
r4r0-execution-service   |     "reduceOnly": null,
r4r0-execution-service   |     "side": "sell",
r4r0-execution-service   |     "price": 88175.29,
r4r0-execution-service   |     "triggerPrice": null,
r4r0-execution-service   |     "amount": 0.00016,
r4r0-execution-service   |     "cost": 14.1080464,
r4r0-execution-service   |     "average": 88175.29,
r4r0-execution-service   |     "filled": 0.00016,
r4r0-execution-service   |     "remaining": 0.0,
r4r0-execution-service   |     "status": "closed",
r4r0-execution-service   |     "fee": {
r4r0-execution-service   |       "currency": "USDT",
r4r0-execution-service   |       "cost": 0.01410805
r4r0-execution-service   |     },
r4r0-execution-service   |     "trades": [
r4r0-execution-service   |       {
r4r0-execution-service   |         "info": {
r4r0-execution-service   |           "price": "88175.29000000",
r4r0-execution-service   |           "qty": "0.00016000",
r4r0-execution-service   |           "commission": "0.01410805",
r4r0-execution-service   |           "commissionAsset": "USDT",
r4r0-execution-service   |           "tradeId": "5724807603"
r4r0-execution-service   |         },
r4r0-execution-service   |         "timestamp": null,
r4r0-execution-service   |         "datetime": null,
r4r0-execution-service   |         "symbol": "BTC/USDT",
r4r0-execution-service   |         "id": "5724807603",
r4r0-execution-service   |         "order": null,
r4r0-execution-service   |         "type": null,
r4r0-execution-service   |         "side": null,
r4r0-execution-service   |         "takerOrMaker": null,
r4r0-execution-service   |         "price": 88175.29,
r4r0-execution-service   |         "amount": 0.00016,
r4r0-execution-service   |         "cost": 14.1080464,
r4r0-execution-service   |         "fee": {
r4r0-execution-service   |           "cost": 0.01410805,
r4r0-execution-service   |           "currency": "USDT"
r4r0-execution-service   |         },
r4r0-execution-service   |         "fees": [
r4r0-execution-service   |           {
r4r0-execution-service   |             "cost": 0.01410805,
r4r0-execution-service   |             "currency": "USDT"
r4r0-execution-service   |           }
r4r0-execution-service   |         ]
r4r0-execution-service   |       }
r4r0-execution-service   |     ],
r4r0-execution-service   |     "fees": [
r4r0-execution-service   |       {
r4r0-execution-service   |         "currency": "USDT",
r4r0-execution-service   |         "cost": 0.01410805
r4r0-execution-service   |       }
r4r0-execution-service   |     ],
r4r0-execution-service   |     "stopPrice": null,
r4r0-execution-service   |     "takeProfitPrice": null,
r4r0-execution-service   |     "stopLossPrice": null
r4r0-execution-service   |   }
r4r0-execution-service   | }