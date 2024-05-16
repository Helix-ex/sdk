import asyncio
import configparser
from pathlib import Path
import math
import pandas as pd
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from HelixTokens import HelixTokens, get_base_currency, get_quote_currency
from Ordergateway import Ordergateway
from Helpers.FundingWallet import FundingWallet
from Helpers.TradingWallet import TradingWallet
from Trading.Swap import Swap
from Trading.Twap import Twap

def round_down(value: float, digits: int) -> float:
    pow: int = 10 ** digits
    return math.floor(value * pow) / pow

async def main():

    config_file = Path('helix_secret.cfg')
    if config_file.is_file() == False:
        print('helix_secret.cfg not found')
        return
    config = configparser.ConfigParser()
    config.read('helix_secret.cfg')
    config_sections = config.sections()
    if 'trading' not in config_sections:
        print('[trading] section not found in helix_secret.cfg')
        return

    if 'asset' not in config['trading']:
        print('asset not found in [trading] section of helix_secret.cfg')
        return
    _asset = config['trading']['asset']
    _base_currency = get_base_currency(config['trading']['asset'])
    if not _base_currency:
        print(f"Unsupported base asset: {config['trading']['asset']}")
        return
    _base_helix_token = HelixTokens[_base_currency]
    _base_qty_num_digits = int(HelixTokens[_base_currency]['qty_num_digits'])
    if 'strategy' not in config['trading']:
        print('strategy not found in [trading] section of helix_secret.cfg')
        return
    _strategy = config['trading']['strategy']
    if 'amount' not in config['trading']:
        print('amount not found in [trading] section of helix_secret.cfg')
        return
    _base_amount = float(config['trading']['amount'])
    _quote_currency = get_quote_currency(config['trading']['asset'])
    if not _quote_currency:
        print(f"Unsupported quote asset: {config['trading']['asset']}")
        return
    _quote_helix_token = HelixTokens[_quote_currency]
    _quote_qty_num_digits = int(HelixTokens[_quote_currency]['qty_num_digits'])
    if 'side' not in config['trading']:
        print('side not found in [trading] section of helix_secret.cfg')
        return    
    _side = config['trading']['side']
    if 'twap_duration' not in config['trading']:
        print('twap_duration not found in [trading] section of helix_secret.cfg')
        return
    _twap_duration = float(config['trading']['twap_duration'])
    if 'twap_num_intervals' not in config['trading']:
        print('twap_num_intervals not found in [trading] section of helix_secret.cfg')
        return
    _twap_num_intervals = int(config['trading']['twap_num_intervals'])
   
    if 'withdraw_external_label' not in config['trading']:
        _withdraw_external_label = None
    else:
        _withdraw_external_label = config['trading']['withdraw_external_label']
    _report_log = []

    _Ordergateway = Ordergateway()
    if await _Ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        fundingWallet = FundingWallet()
        tradingWallet = TradingWallet(_Ordergateway)

        base_currency = _base_currency.upper()
        quote_currency = _quote_currency.upper()
        if (_side.upper() == 'SELL'):
            base_side = 'SELL'
            quote_side = 'BUY'
        else:
            base_side = 'BUY'
            quote_side = 'SELL'

        # step 1: check if trading wallet has enough trading balance
        trading_balance = tradingWallet.GetBalances(asset=_base_currency)
        if trading_balance is not None and trading_balance >= _base_amount:
            print(f'Trading wallet has enough balance of {_base_currency} {_base_amount}')
        else:
            # step 2: transfer funding to trading wallet, waiting for deposit if needed
            enough_funding_balance = await fundingWallet.WaitUntilBalance(_base_currency, _base_amount)
            if not enough_funding_balance:
                return
            # take off network fees
            #fee_estimates = fundingWallet.GetFeeEstimates(_base_helix_token)
            #service_fee = float(fee_estimates['service_fee'])
            transfer_amount = round(_base_amount, _base_qty_num_digits)
            print(f'\nTransferring {base_currency} {_base_amount:,} from funding to trading wallet...')
            print(f'  Transfer Amount: {transfer_amount:,.4f}')
            #print(f'  Service Fee: {service_fee:,.4f}')
            fund_to_trade = await fundingWallet.ExecuteTransfer(_base_helix_token, _base_amount, 'fund_to_trade')
            if not fund_to_trade:
                return
            _report_log.append(fund_to_trade)
            # step 3: wait for trading wallet balance
            enough_trading_balance = await tradingWallet.WaitUntilBalance(_base_currency, _base_amount)
            if not enough_trading_balance:
                return

        # step 4: execute trading strategy
        if _strategy == 'swap':
            swap = Swap(_Ordergateway)
            trades = await swap.ExecuteSwap(_asset, _side, _base_amount)
            if not trades:
                return
        elif _strategy == 'twap':
            twap = Twap(_Ordergateway)
            trades = await twap.ExecuteTwap(_asset, _side, _base_amount, _twap_duration, _twap_num_intervals)
            if not trades:
                return
        else:
            print(f"Invalid strategy: {_strategy}")
            return
        _report_log.append(trades)
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
        # keep track of commission in quote currency as they will need to be deducted from the proceeds
        quote_currency_comission = 0
        for commission_asset in commissions_totals['amount']:
            if commission_asset == _quote_currency.upper():
                quote_currency_comission += float(commissions_totals['amount'][commission_asset])
            print(f"  {commission_asset}: {commissions_totals['amount'][commission_asset]:,.4f}")

        # step 5: transfer trading wallet to funding wallet
        quote_amount = round_down(quoteTradedQty - quote_currency_comission, _quote_qty_num_digits)
        # take off network fees
        fee_estimates = tradingWallet.GetFeeEstimates(_quote_helix_token)
        service_fee = float(fee_estimates['service_fee'])
        transfer_amount = round(quote_amount - service_fee, _quote_qty_num_digits)
        print(f'\nTransferring {quote_currency} {quote_amount:,} from trading to funding wallet...')
        print(f'  Transfer Amount: {transfer_amount:,.4f}')
        print(f'  Service Fee: {service_fee:,.4f}')
        trade_to_fund = await tradingWallet.ExecuteTransfer(_quote_helix_token, transfer_amount, 'trade_to_fund')
        if not trade_to_fund:
            return
        _report_log.append(trade_to_fund)
        
        # step 6: transfer from funding wallet to external wallet
        if _withdraw_external_label:
            withdraw_amount = transfer_amount
            #fee_estimates = fundingWallet.GetFeeEstimates(_quote_helix_token)
            #service_fee = float(fee_estimates['service_fee'])
            transfer_amount = round(withdraw_amount, _quote_qty_num_digits)
            print(f'\nTransferring {quote_currency} {withdraw_amount:,} from funding to external wallet...')
            print(f'  Transfer Amount: {transfer_amount:,.4f}')
            #print(f'  Service Fee: {service_fee:,.4f}')
            fund_to_external = await fundingWallet.ExecuteTransfer(_quote_helix_token, transfer_amount, 'fund_to_external', _withdraw_external_label)
            if not fund_to_external:
                return
            _report_log.append(fund_to_external)
    finally:
        _Ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())