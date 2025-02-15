import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from alpaca_trade_api.rest import REST, TimeFrame
import time
#0b84846d-9074-4b95-b417-5f4944e7c2bc
# Alpaca API Credentials
API_KEY = 'PKOI7JFS6ZBSLVSNZ2RO'
API_SECRET = 'TgTD17y9j31iCryf7XazMzkgEgzSAScxePySSYra'
BASE_URL = 'https://paper-api.alpaca.markets'  # Use paper trading URL for testing

# Alpaca API Client
alpaca = REST(API_KEY, API_SECRET, BASE_URL)


def fetch_historical_data(symbol, timeframe, limit=1000):
    # Fetch historical market data using Alpaca
    barset = alpaca.get_bars(
        symbol,
        TimeFrame.Minute if timeframe == '1m' else TimeFrame.Hour,
        limit=limit
    )
    print(barset.head())  # Debugging: Check the structure of the data
    return barset
    data = pd.DataFrame([bar._raw for bar in barset])
    data.rename(columns={'t': 'timestamp', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'}, inplace=True)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
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
    balance = initial_balance
    position = 0  # Current holdings
    for i in range(len(data) - 1):
        if data['Signal'].iloc[i] == 1:  # Buy Signal
            position = balance / data['close'].iloc[i]
            balance = 0
        elif data['Signal'].iloc[i] == -1 and position > 0:  # Sell Signal
            balance = position * data['close'].iloc[i]
            position = 0

    # Final balance
    if position > 0:
        balance = position * data['close'].iloc[-1]

    return balance


def execute_trade(symbol, signal, balance):
    if signal == 1:  # Buy
        try:
            qty = balance / float(alpaca.get_last_trade(symbol).price)
            order = alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print(f"BUY Order Executed: {order}")
        except Exception as e:
            print(f"Error executing BUY order: {e}")
    elif signal == -1:  # Sell
        try:
            position = float(alpaca.get_position(symbol).qty)
            order = alpaca.submit_order(
                symbol=symbol,
                qty=position,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print(f"SELL Order Executed: {order}")
        except Exception as e:
            print(f"Error executing SELL order: {e}")


if __name__ == "__main__":
    # Parameters
    symbol = 'BTCUSD'
    timeframe = '1h'
    initial_balance = 1000

    # Fetch historical data
    data = fetch_historical_data(symbol, timeframe)

    # Choose strategy
    data = macd_strategy(data)

    # Backtest
    final_balance = backtest(data, initial_balance)
    print(f"Final Balance after Backtesting: ${final_balance:.2f}")

    # Live Trading
    while True:
        try:
            live_data = fetch_historical_data(symbol, timeframe, limit=50)
            strategy_data = macd_strategy(live_data)
            signal = strategy_data['MACD_Strategy_Signal'].iloc[-1]
            execute_trade(symbol, signal, initial_balance)
            time.sleep(60 * 60)  # Wait for the next hour
        except Exception as e:
            print(f"Error in live trading loop: {e}")
