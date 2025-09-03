# test_price.py
import sys
import os

# Add parent directory to path to import api module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import fmp_api


def test_get_current_price():
    """Test the get_current_price function with different tickers"""

    test_tickers = ["AAPL", "MSFT", "EVVTY", "PYPL"]

    print("Testing get_current_price function...")
    print("=" * 50)

    for ticker in test_tickers:
        print(f"\nTesting ticker: {ticker}")
        print("-" * 30)

        try:
            # Test the function
            result = fmp_api.get_current_price(ticker)

            print(f"Raw result: {result}")
            print(f"Type of result: {type(result)}")

            if result:
                print(f"Length: {len(result)}")

                if len(result) >= 1:
                    price = result[0]
                    timestamp = result[1] if len(result) > 1 else None

                    print(f"Price: {price}")
                    print(f"Timestamp: {timestamp}")

                    if price is not None:
                        try:
                            price_float = float(price)
                            print(f"Price as float: {price_float}")
                        except ValueError as e:
                            print(f"Cannot convert price to float: {e}")
                    else:
                        print("Price is None")
                else:
                    print("Result has no elements")
            else:
                print("Result is None or empty")

        except Exception as e:
            print(f"Error testing {ticker}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 50)
    print("Test completed")


if __name__ == "__main__":
    test_get_current_price()
