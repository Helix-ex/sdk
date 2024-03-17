import asyncio
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Ordergateway import Ordergateway
from HelixTokens import HelixTokens
from Helpers.TradingWallet import TradingWallet

async def main():

    ordergateway = Ordergateway()
    if await ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        tradingWallet = TradingWallet(ordergateway)

        balances = tradingWallet.GetBalances()
        if balances:
            print(f'\nTrading wallet balances: {balances}')

        icp_balance = tradingWallet.GetBalances(asset='HTICP')
        if icp_balance:
            print(f'\nHTICP: {icp_balance}')

        funding_to_trading = tradingWallet.GetTransfers(asset='HTICP', kind='fund_to_trade')
        if funding_to_trading:
            # display all the transfers
            print(f'\nFunding to trading: {funding_to_trading}')

        trading_to_funding = tradingWallet.GetTransfers(asset='HTICP', kind='trade_to_fund')
        if trading_to_funding:
            # display the first transfer
            first_transfer = trading_to_funding[0]
            transfer_id = first_transfer['id']
            transfer = tradingWallet.GetTransfers(id=transfer_id)
            if transfer:
                print(f'\nTransfer: {transfer}')

        active_transfers = tradingWallet.GetActiveTransfers(asset='HTICP')
        if active_transfers is not None:
            print(f'\nActive transfers: {active_transfers}')

        fees = tradingWallet.GetFeeEstimates(HelixTokens['hticp'])
        if fees:
            print(f'\nFee estimates: {fees}')
    finally:
        ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())