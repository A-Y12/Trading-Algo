import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator
import ccxt  # For broker integration
import time
from ta.trend import SMAIndicator, EMAIndicator, MACD


def fetch_historical_data(symbol, timeframe, limit=1000):
    # Example using Binance API via CCXT
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)
    return data


def moving_average_crossover_strategy(data, short_window=9, long_window=21):
    data['SMA_Short'] = SMAIndicator(data['close'], window=short_window).sma_indicator()
    data['SMA_Long'] = SMAIndicator(data['close'], window=long_window).sma_indicator()

    # Generate signals
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1  # Buy
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1  # Sell

    return data


def rsi_strategy(data, rsi_window=14, overbought=70, oversold=30):
    data['RSI'] = RSIIndicator(data['close'], window=rsi_window).rsi()

    # Generate signals
    data['Signal'] = 0
    data.loc[data['RSI'] < oversold, 'Signal'] = 1  # Buy
    data.loc[data['RSI'] > overbought, 'Signal'] = -1  # Sell

    return data


def macd_strategy(data):
    macd = MACD(data['close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal_Line'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    data['MACD_Strategy_Signal'] = 0
    data.loc[data['MACD'] > data['MACD_Signal_Line'], 'MACD_Strategy_Signal'] = 1  # Buy
    data.loc[data['MACD'] < data['MACD_Signal_Line'], 'MACD_Strategy_Signal'] = -1  # Sell
    return data


def backtest(data, initial_balance=1000):
    # balance = initial_balance
    # position = 0  # Current holdings
    # for i in range(len(data) - 1):
    #     if data['Signal'].iloc[i] == 1:  # Buy Signal
    #         position = balance / data['close'].iloc[i]
    #         balance = 0
    #     elif data['Signal'].iloc[i] == -1 and position > 0:  # Sell Signal
    #         balance = position * data['close'].iloc[i]
    #         position = 0
    #
    # # Final balance
    # if position > 0:
    #     balance = position * data['close'].iloc[-1]
    #
    # return balance
        balance = initial_balance
        position = 0  # Current holdings
        for i in range(len(data) - 1):
            if data['MACD_Strategy_Signal'].iloc[i] == 1:  # Buy Signal
                position = balance / data['close'].iloc[i]
                balance = 0
            elif data['MACD_Strategy_Signal'].iloc[i] == -1 and position > 0:  # Sell Signal
                balance = position * data['close'].iloc[i]
                position = 0

        # Final balance
        if position > 0:
            balance = position * data['close'].iloc[-1]

        return balance


def execute_trade(symbol, signal, balance, exchange):
    if signal == 1:  # Buy
        order = exchange.create_market_buy_order(symbol, balance / exchange.fetch_ticker(symbol)['close'])
        print(f"BUY Order Executed: {order}")
    elif signal == -1:  # Sell
        order = exchange.create_market_sell_order(symbol, balance / exchange.fetch_ticker(symbol)['close'])
        print(f"SELL Order Executed: {order}")


if __name__ == "__main__":
    # Parameters
    symbol = 'BTC/USDT'
    timeframe = '1h'
    initial_balance = 1000

    # Fetch historical data
    data = fetch_historical_data(symbol, timeframe)

    # Choose strategy
    # data = moving_average_crossover_strategy(data)  # SMA crossover
    # data = rsi_strategy(data)  # RSI-based
    data = macd_strategy(data)

    # Backtest
    final_balance = backtest(data, initial_balance)
    print(f"Final Balance after Backtesting: ${final_balance:.2f}")

    # Live Trading (Optional)
    # exchange = ccxt.binance({
    #     'apiKey': 'your_api_key',
    #     'secret': 'your_api_secret',
    # })
    # while True:
    #     live_data = fetch_historical_data(symbol, timeframe, limit=50)
    #     strategy_data = moving_average_crossover_strategy(live_data)
    #     signal = strategy_data['Signal'].iloc[-1]
    #     execute_trade(symbol, signal, initial_balance, exchange)
    #     time.sleep(60 * 60)  # Wait for the next hour


# plt.figure(figsize=(14, 7))
# plt.plot(data['close'], label='Close Price', alpha=0.5)
# plt.plot(data['SMA_Short'], label='SMA Short', alpha=0.75)
# plt.plot(data['SMA_Long'], label='SMA Long', alpha=0.75)
# plt.title("Moving Average Crossover Strategy")
# plt.legend()
# plt.show()


# import matplotlib.pyplot as plt
#
# # Visualization
# plt.figure(figsize=(14, 8))
#
# # Plot Close Prices
# plt.subplot(2, 1, 1)
# plt.plot(data.index, data['close'], label='Close Price', color='blue', alpha=0.7)
# plt.scatter(data.index[data['Signal'] == 1], data['close'][data['Signal'] == 1],
#             label='Buy Signal', marker='^', color='green', alpha=1)
# plt.scatter(data.index[data['Signal'] == -1], data['close'][data['Signal'] == -1],
#             label='Sell Signal', marker='v', color='red', alpha=1)
# plt.title("RSI-Based Trading Strategy - Close Prices")
# plt.xlabel("Date")
# plt.ylabel("Price")
# plt.legend()
#
# # Plot RSI
# plt.subplot(2, 1, 2)
# plt.plot(data.index, data['RSI'], label='RSI', color='orange', alpha=0.7)
# plt.axhline(70, linestyle='--', color='red', label='Overbought (70)')
# plt.axhline(30, linestyle='--', color='green', label='Oversold (30)')
# plt.fill_between(data.index, 30, 70, color='gray', alpha=0.1)
# plt.title("RSI Indicator")
# plt.xlabel("Date")
# plt.ylabel("RSI")
# plt.legend()
#
# plt.tight_layout()
# plt.show()

plt.subplot(3, 1, 3)
plt.plot(data.index, data['MACD'], label='MACD', color='blue', alpha=0.7)
plt.plot(data.index, data['MACD_Signal_Line'], label='Signal Line', color='red', alpha=0.7)
plt.bar(data.index, data['MACD_Hist'], label='MACD Histogram', color='gray', alpha=0.5)
plt.scatter(data.index[data['MACD_Strategy_Signal'] == 1], data['MACD'][data['MACD_Strategy_Signal'] == 1],
            label='Buy Signal (MACD)', marker='^', color='green', alpha=1)
plt.scatter(data.index[data['MACD_Strategy_Signal'] == -1], data['MACD'][data['MACD_Strategy_Signal'] == -1],
            label='Sell Signal (MACD)', marker='v', color='red', alpha=1)
plt.title("MACD-Based Strategy")
plt.xlabel("Date")
plt.ylabel("MACD")
plt.legend()

plt.tight_layout()
plt.show()

