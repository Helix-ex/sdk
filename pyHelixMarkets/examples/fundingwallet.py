import asyncio
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Helpers.FundingWallet import FundingWallet

async def main():

    fundingWallet = FundingWallet()

    balances = fundingWallet.GetBalances()
    if balances:
        print(f'\nFunding wallet balances: {balances}')

    icp_balance = fundingWallet.GetBalances(asset='HTICP')
    if icp_balance:
        print(f'\nHTICP: {icp_balance}')

    deposits = fundingWallet.GetTransfers(asset='HTICP', kind='external_to_fund')
    if deposits:
        print(f'\nDeposits: {deposits}')

    funding_to_trading = fundingWallet.GetTransfers(asset='HTICP', kind='fund_to_trade')
    if funding_to_trading:
        print(f'\nFunding to trading: {funding_to_trading}')

    #trading_to_funding = fundingWallet.GetTransfers(asset='HTICP', kind='trade_to_fund')
    trading_to_funding = fundingWallet.GetTransfers()
    if trading_to_funding:
        # display the first transfer
        first_transfer = trading_to_funding[0]
        transfer_id = first_transfer['id']
        transfer = fundingWallet.GetTransfers(id=transfer_id)
        if transfer:
            print(f'\nTransfer: {transfer}')

    withdraws = fundingWallet.GetTransfers(asset='HTICP', kind='fund_to_external')
    if withdraws:
        print(f'\nWithdraws: {withdraws}')

    active_transfers = fundingWallet.GetActiveTransfers(asset='HTICP')
    if active_transfers is not None:
        print(f'\nActive transfers: {active_transfers}')

if __name__ == "__main__":
    asyncio.run(main())