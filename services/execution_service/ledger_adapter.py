import logging
from datetime import datetime

logger = logging.getLogger("execution-service.ledger-adapter")

class LedgerAwareAdapter:
    """
    ExchangeAdapterClient를 래핑하여 모든 트레이딩 활동을 
    봇 서비스(BotService)의 원장(Ledger)에 자동으로 기록하는 어댑터입니다.
    
    모든 전략(Strategy)은 원본 어댑터 대신 이 클래스를 사용하여 
    매매 주문과 체결 내역이 이중 원장(Double-Entry Ledger) 시스템에 
    누락 없이 기록되도록 보장해야 합니다.
    """
    def __init__(self, raw_adapter, bot_client, bot_id):
        self.adapter = raw_adapter
        self.bot_client = bot_client
        self.bot_id = bot_id

    # Passthrough methods for read-only operations
    async def get_balance(self, key_id):
        return await self.adapter.get_balance(key_id)

    async def get_ticker(self, key_id, symbol):
        return await self.adapter.get_ticker(key_id, symbol)

    # 트랜잭션 메서드 (매매 실행 및 기록)
    async def place_order(self, key_id, symbol, side, amount, order_type='market', price=None, reason="Strategy Signal"):
        """
        주문을 실행하고 전체 과정을 이중 원장(Double-Entry Ledger)에 기록합니다.
        단계: 1. 로컬 주문 생성(의도) -> 2. 거래소 주문 실행 -> 3. 체결 내역 기록(확정)
        """
        logger.info(f"원장 트랜잭션 준비 중: {side} {amount} {symbol} (사유: {reason})")

        # 1. PREPARE: 로컬 주문 기록 (매매 의도 저장)
        try:
            local_order = await self.bot_client.create_local_order(
                bot_id=self.bot_id,
                symbol=symbol,
                side=side.upper(),
                quantity=amount,
                reason=reason,
                timestamp=datetime.utcnow()
            )
            
            if not local_order:
                raise Exception("로컬 주문 레코드 생성 실패")
            
            logger.info(f"✅ [1/3] 원장 준비(PREPARE): 로컬 주문 생성됨 (ID: {local_order['id']}, 상태: {local_order['status']})")
            
        except Exception as e:
            logger.error(f"❌ 원장 준비 실패: {e}")
            return {"status": "failed", "reason": "Ledger Prepare Failed"}

        # 2. EXECUTE: 거래소 어댑터 호출 (실제 매매)
        try:
            exchange_order = await self.adapter.place_order(
                key_id=key_id,
                symbol=symbol,
                side=side,
                amount=amount,
                order_type=order_type,
                price=price
            )
            
            # [디버그] 응답 JSON 구조 파악을 위해 로우 데이터 로깅
            import json
            try:
                # datetime 객체 등이 있을 경우를 대비해 default=str 사용
                raw_log = json.dumps(exchange_order, default=str, indent=2)
                logger.info(f"🔍 [거래소 원본 응답]:\n{raw_log}")
            except Exception as log_err:
                logger.error(f"원본 응답 로깅 실패: {log_err}")

            logger.info(f"✅ [2/3] 거래소 실행(EXECUTE): 주문 전송 완료 (ID: {exchange_order.get('id')}, 상태: {exchange_order.get('status')})")
            
        except Exception as e:
            logger.error(f"❌ 거래소 실행 실패: {e}")
            # 실행 실패 시 로컬 주문 상태를 FAILED로 업데이트
            await self.bot_client.update_order_status(local_order["id"], "FAILED")
            return {"status": "failed", "reason": str(e)}

        # 3. COMMIT: 글로벌 체결 내역 기록 (멀티 Fill 지원)
        if exchange_order.get("status") == "filled":
            try:
                details = exchange_order.get("details", {})
                info = details.get("info", {})
                fills = info.get("fills", [])
                
                # 바이낸스 등: fills 배열이 있는 경우 (부분 체결 합산)
                if fills:
                    for fill in fills:
                        price = float(fill.get("price", 0.0))
                        qty = float(fill.get("qty", 0.0))
                        quote_qty = price * qty
                        
                        # 거래소 체결 시간(transactTime)을 사용, 없으면 현재 시간
                        ts_val = info.get("transactTime")
                        if ts_val:
                            # ms 단위를 ISO 포맷으로 변환
                            ts_iso = datetime.utcfromtimestamp(int(ts_val)/1000).isoformat()
                        else:
                            ts_iso = datetime.utcnow().isoformat()

                        payload = {
                            "local_order_id": local_order["id"],
                            "exchange_trade_id": str(fill.get("tradeId")),
                            "exchange_order_id": str(exchange_order.get("id")),
                            "order_list_id": str(info.get("orderListId")),
                            "symbol": symbol,
                            "side": info.get("side", side).upper(),
                            "price": price,
                            "quantity": qty,
                            "quote_qty": quote_qty,
                            "fee": float(fill.get("commission", 0.0)),
                            "fee_asset": fill.get("commissionAsset"),
                            "timestamp": ts_iso
                        }
                        
                        await self.bot_client.record_execution(payload)
                        logger.info(f"✅ [3/3] 원장 커밋(COMMIT): 체결 내역 기록됨 {payload['exchange_trade_id']}")

                # Fallback: Fills가 없는 경우 (예: 시뮬레이션 환경, 일부 거래소)
                else:
                    logger.warning("⚠️ 응답에 'fills' 데이터가 없습니다. 집계된 체결 데이터를 사용합니다.")
                    payload = {
                        "local_order_id": local_order["id"],
                        "exchange_trade_id": str(exchange_order.get("id")), # 대체 ID 사용
                        "exchange_order_id": str(exchange_order.get("id")),
                        "order_list_id": None,
                        "symbol": symbol,
                        "side": side.upper(),
                        "price": exchange_order.get("average") or exchange_order.get("price", 0.0),
                        "quantity": exchange_order.get("filled", amount),
                        "quote_qty": (exchange_order.get("cost") or 0.0),
                        "fee": exchange_order.get("fee", {}).get("cost", 0.0),
                        "fee_asset": exchange_order.get("fee", {}).get("currency"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.bot_client.record_execution(payload)
                    logger.info(f"✅ [3/3] 원장 커밋(COMMIT): 집계된 체결 내역 기록됨")
                
                await self.bot_client.update_order_status(local_order["id"], "FILLED")
            
            except Exception as e:
                logger.error(f"❌ 원장 커밋 실패 (심각한 오류): {e}")
        elif exchange_order.get("status") in ["error", "failed"]:
             await self.bot_client.update_order_status(local_order["id"], "FAILED")
             logger.error(f"❌ [3/3] 원장 업데이트: 주문 실행 실패 (상태: {exchange_order.get('status')})")
        else:
             await self.bot_client.update_order_status(local_order["id"], "SENT")
             logger.warning(f"⚠️ [3/3] 원장 업데이트: 즉시 체결되지 않음 (상태: SENT)")
        
        return exchange_order
