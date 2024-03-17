import asyncio
import json
import os
import sys
import math
import pandas as pd

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Ordergateway import Ordergateway
from HelixTokens import HelixTokens, get_base_currency, get_quote_currency
from Trading.Twap import Twap

def round_down(value: float, digits: int) -> float:
    pow: int = 10 ** digits
    return math.floor(value * pow) / pow

async def main():

    # TWAP parameters
    _asset = 'CKBTC/USDC'
    _side = 'buy'
    _base_amount = 0.025
    # in hours. 1/60 = 1 minute
    _twap_duration = 2 / 60
    _twap_num_intervals = 5

    _Ordergateway = Ordergateway()
    if await _Ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        _base_currency = get_base_currency(_asset)
        if not _base_currency:
            print(f"Unsupported base asset: {_asset}")
            return
        _quote_currency = get_quote_currency(_asset)
        if not _quote_currency:
            print(f"Unsupported quote asset: {_asset}")
            return
        _quote_qty_num_digits = int(HelixTokens[_quote_currency]['qty_num_digits'])

        twap = Twap(_Ordergateway)
        trades = await twap.ExecuteTwap(_asset, _side, _base_amount, _twap_duration, _twap_num_intervals)
        if not trades:
            return

        base_currency = _base_currency.upper()
        quote_currency = _quote_currency.upper()
        if (_side.upper() == 'SELL'):
            base_side = 'SELL'
            quote_side = 'BUY'
        else:
            base_side = 'BUY'
            quote_side = 'SELL'

        # execution summary
        orderTrades = [trade for trade in trades if 'msg' in trade and trade['msg'] == 'OrderTrade' and 'status' in trade and trade['status'] == 'filled']
        baseTradedQty = sum([float(trade['cumTradedQty']) for trade in orderTrades])
        if _base_amount != baseTradedQty:
            print(f"Warning: expected {base_side} {base_currency} {_base_amount} found traded only {baseTradedQty}")
            return
        quoteTradedQty = round_down(sum([float(trade['quoteCumTradedQty']) for trade in orderTrades]), _quote_qty_num_digits)
        print(f'\nExecution Summary:')
        print(f'  {base_currency}: {base_side} {baseTradedQty:,}')
        print(f'  {quote_currency}: {quote_side} {quoteTradedQty:,.4f}')
        avgPrice = quoteTradedQty / baseTradedQty
        print(f'  Average {base_side} Price: {avgPrice:,.4f}')
        # flattens the commissions to list
        commissions = [i for row in [trade['commissions'] for trade in trades] for i in row]
        # convert list of dict to dataframe
        df = pd.DataFrame(commissions)
        # convert amount to numeric
        df['amount'] = pd.to_numeric(df['amount'])
        # sum the amount by asset
        commissions_totals = df.groupby('asset').sum().to_dict()
        print('\nCommissions:')
        for commission_asset in commissions_totals['amount']:
            print(f"  {commission_asset}: {commissions_totals['amount'][commission_asset]:,.4f}")
    finally:
        _Ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())