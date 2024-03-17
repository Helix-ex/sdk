import asyncio
import os
import sys
import requests
import json
import math

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Ordergateway import Ordergateway
from HelixTokens import HelixTokens
from Helpers.TradingWallet import TradingWallet

_shutdown = False
_binance_symbol = "ICPUSDT"
_helix_symbol = "HTICPUSDC"
_helix_price_num_digits = 3
_bid_spread = 0.0050
_bid_size = 1.0
_ask_spread = 0.0050
_ask_size = 1.0
_binance_best_bid: float = 0.0
_binance_best_ask: float = 0.0

async def get_binance_price(symbol):
    global _shutdown
    global _binance_best_bid, _binance_best_ask

    url = 'https://api.binance.com/api/v3/ticker/bookTicker'
    params = {'symbol': symbol}
    while not _shutdown:
        response_json = requests.get(url, params=params)
        if (response_json.status_code != 200):
            print(f'Error getting price from Binance: {response_json.status_code}')
            await asyncio.sleep(2)
            continue

        response = json.loads(response_json.text)
        if 'bidPrice' in response:
            _binance_best_bid = float(response['bidPrice'])
        if 'askPrice' in response:
            _binance_best_ask = float(response['askPrice'])
        await asyncio.sleep(1)

def round_down(value: float, digits: int) -> float:
    pow: int = 10 ** digits
    return math.floor(value * pow) / pow

def round_up(value: float, digits: int) -> float:
    pow: int = 10 ** digits
    return math.ceil(value * pow) / pow

async def main():
    global _shutdown
    global _binance_symbol, _helix_symbol, _bid_spread, _bid_size, _ask_spread, _ask_size
    global _binance_best_bid, _binance_best_ask

    _shutdown = False
    asyncio.create_task(get_binance_price(_binance_symbol))

    ordergateway = Ordergateway()
    if await ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        tradingWallet = TradingWallet(ordergateway)

        last_binance_bid = 0.0
        buy_clientOrderId = None
        last_binance_ask = 0.0
        sell_clientOrderId = None
        while True:
            price_updated = False
            if last_binance_bid != _binance_best_bid:
                helix_bid = round_down(_binance_best_bid * (1 - _bid_spread), _helix_price_num_digits)
                # cancel old order before placing new order
                order_type = 'New order'
                if buy_clientOrderId:
                    await tradingWallet.CancelOrder(_helix_symbol, buy_clientOrderId)
                    order_type = 'Replace order'
                buy_clientOrderId = await tradingWallet.NewOrder(_helix_symbol, 'limit', 'buy', timeInForce='gtc', price=helix_bid, totalQuantity=_bid_size)
                print(f'{order_type} BUY {_bid_size} @ helix={helix_bid} binance={_binance_best_bid} id={buy_clientOrderId}')
                price_updated = True
                last_binance_bid = _binance_best_bid
            if last_binance_ask != _binance_best_ask:
                helix_ask = round_up(_binance_best_ask * (1 + _ask_spread), _helix_price_num_digits)
                order_type = 'New order'
                if sell_clientOrderId:
                    await tradingWallet.CancelOrder(_helix_symbol, sell_clientOrderId)
                    order_type = 'Replace order'
                sell_clientOrderId = await tradingWallet.NewOrder(_helix_symbol, 'limit', 'sell', timeInForce='gtc', price=helix_ask, totalQuantity=_ask_size)
                print(f'{order_type} SELL {_ask_size} @ helix={helix_ask} binance={_binance_best_ask} id={buy_clientOrderId}')
                price_updated = True
                last_binance_ask = _binance_best_ask

            if not price_updated:
                await asyncio.sleep(1)
    finally:
        _shutdown = True
        ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())