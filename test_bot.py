#!/usr/bin/env python3
"""
Test script for Polymarket Arbitrage Bot
Validates all components and functionality
"""
import sys
import asyncio
from pathlib import Path

# Add the app directory to path
app_dir = Path(__file__).parent / "polymarket-arbitrage-bot" / "app"
sys.path.insert(0, str(app_dir))

def test_imports():
    """Test all module imports"""
    print("🧪 Testing module imports...")
    
    try:
        from src.utils.config import config
        print("  ✅ Config module")
    except Exception as e:
        print(f"  ❌ Config module: {e}")
        return False
    
    try:
        from src.utils.logger import setup_logger
        print("  ✅ Logger module")
    except Exception as e:
        print(f"  ❌ Logger module: {e}")
        return False
    
    try:
        from src.core.market import PolymarketAPI, Market
        print("  ✅ Market module")
    except Exception as e:
        print(f"  ❌ Market module: {e}")
        return False
    
    try:
        from src.core.arbitrage import ArbitrageDetector
        print("  ✅ Arbitrage module")
    except Exception as e:
        print(f"  ❌ Arbitrage module: {e}")
        return False
    
    try:
        from src.core.demo_mode import DemoMode
        print("  ✅ Demo mode module")
    except Exception as e:
        print(f"  ❌ Demo mode module: {e}")
        return False
    
    try:
        import PyQt6
        print("  ✅ PyQt6 GUI framework")
    except Exception as e:
        print(f"  ❌ PyQt6: {e}")
        return False
    
    return True


def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.utils.config import config
        
        # Test basic config values
        assert config.min_profit >= 0, "Invalid min_profit"
        assert 0 <= config.trading_fee <= 1, "Invalid trading_fee"
        assert config.gas_estimate >= 0, "Invalid gas_estimate"
        assert config.demo_balance > 0, "Invalid demo_balance"
        
        print(f"  ✅ Min profit: ${config.min_profit}")
        print(f"  ✅ Trading fee: {config.trading_fee * 100}%")
        print(f"  ✅ Gas estimate: ${config.gas_estimate}")
        print(f"  ✅ Demo balance: ${config.demo_balance}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_arbitrage_logic():
    """Test arbitrage detection logic"""
    print("\n🧪 Testing arbitrage logic...")
    
    try:
        from src.core.arbitrage import ArbitrageDetector
        
        detector = ArbitrageDetector(min_profit=0.01, trading_fee=0.02, gas_cost=0.01)
        
        # Test case 1: Clear arbitrage opportunity
        opp1 = detector.check_arbitrage("test1", "Test Market 1", 0.40, 0.45)
        if opp1:
            print(f"  ✅ Arbitrage detected: ${opp1.estimated_profit:.4f} profit")
        else:
            print("  ❌ Failed to detect clear arbitrage")
            return False
        
        # Test case 2: No arbitrage (prices too high)
        opp2 = detector.check_arbitrage("test2", "Test Market 2", 0.60, 0.50)
        if opp2 is None:
            print("  ✅ Correctly rejected expensive market")
        else:
            print("  ❌ False positive on expensive market")
            return False
        
        # Test case 3: Invalid inputs
        opp3 = detector.check_arbitrage("", "", -0.1, 1.5)
        if opp3 is None:
            print("  ✅ Correctly rejected invalid inputs")
        else:
            print("  ❌ Failed to validate inputs")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Arbitrage logic error: {e}")
        return False


def test_demo_mode():
    """Test demo trading functionality"""
    print("\n🧪 Testing demo mode...")
    
    try:
        from src.core.demo_mode import DemoMode
        
        demo = DemoMode(initial_balance=1000.0)
        
        # Test initial state
        assert demo.balance == 1000.0, "Invalid initial balance"
        assert demo.total_profit == 0.0, "Invalid initial profit"
        assert demo.num_trades == 0, "Invalid initial trade count"
        print("  ✅ Initial state correct")
        
        # Test valid trade
        initial_balance = demo.balance
        trade1 = demo.execute_arbitrage("Test Market", 0.40, 0.45, 0.02, 0.01)
        if trade1:
            print(f"  ✅ Trade executed: ${trade1.profit:.4f} profit")
            assert demo.num_trades == 1, "Trade count not updated"
            assert demo.balance != initial_balance, "Balance not updated"
        else:
            print("  ❌ Valid trade failed")
            return False
        
        # Test invalid trade (insufficient balance)
        demo.balance = 0.10  # Set very low balance
        trade2 = demo.execute_arbitrage("Test Market 2", 0.40, 0.45, 0.02, 0.01)
        if trade2 is None:
            print("  ✅ Correctly rejected insufficient balance trade")
        else:
            print("  ❌ Failed to validate balance")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Demo mode error: {e}")
        return False


async def test_api_connectivity():
    """Test Polymarket API connectivity"""
    print("\n🧪 Testing API connectivity...")
    
    try:
        from src.core.market import PolymarketAPI
        
        api = PolymarketAPI()
        
        # Test market fetching
        markets = await api.fetch_markets(limit=5)
        if markets and len(markets) > 0:
            print(f"  ✅ Fetched {len(markets)} markets")
            
            # Test market structure
            market = markets[0]
            if market.id and market.question:
                print(f"  ✅ Market data valid: {market.question[:50]}...")
            else:
                print("  ❌ Invalid market data structure")
                await api.close()
                return False
            
            # Test price fetching (if token IDs available)
            if market.yes_token_id:
                price_data = await api.get_live_prices(market.yes_token_id)
                if price_data:
                    print(f"  ✅ Price data: ${price_data['price']:.4f}")
                else:
                    print("  ⚠️  No price data available (may be normal)")
        else:
            print("  ❌ No markets fetched")
            await api.close()
            return False
        
        await api.close()
        return True
        
    except Exception as e:
        print(f"  ❌ API connectivity error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 POLYMARKET ARBITRAGE BOT - TEST SUITE")
    print("=" * 60)
    
    # Change to app directory
    import os
    os.chdir(app_dir)
    
    tests_passed = 0
    total_tests = 5
    
    # Run tests
    if test_imports():
        tests_passed += 1
    
    if test_config():
        tests_passed += 1
    
    if test_arbitrage_logic():
        tests_passed += 1
    
    if test_demo_mode():
        tests_passed += 1
    
    # Run async test
    try:
        if asyncio.run(test_api_connectivity()):
            tests_passed += 1
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
    
    # Results
    print("\n" + "=" * 60)
    print("🧪 TEST RESULTS")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("The bot is ready to use.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above.")
    
    print("=" * 60)
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)