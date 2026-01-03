def test_btc_pnl_logic():
    # Scenario: BTC Trading
    # Prices are large, Quantities are small.
    
    buy_price = 60000.00
    sell_price = 60150.00 # $150 move
    quantity = 0.002 # Small amount
    
    # Expected PnL: $150 * 0.002 = $0.30
    
    pnl = (sell_price - buy_price) * quantity
    
    print(f"Buy Price: ${buy_price}")
    print(f"Sell Price: ${sell_price}")
    print(f"Quantity: {quantity} BTC")
    print(f"Calculated PnL: ${pnl:.4f}")
    
    expected = (60150 - 60000) * 0.002
    print(f"Expected: ${expected:.4f}")
    
    assert abs(pnl - 0.30) < 0.000001
    print("Logic Verification: PASS")

if __name__ == "__main__":
    test_btc_pnl_logic()
