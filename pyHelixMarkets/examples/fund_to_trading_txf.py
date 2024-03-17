import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from HelixTokens import HelixTokens
from Helpers.FundingWallet import FundingWallet

async def main():

    fundingWallet = FundingWallet()
    icp = HelixTokens['icp']

    # do 5 transfers from Funding to Trading
    # each transfer is 0.01 ICP
    for i in range(5):
        print(f'\nTransfer Funding to Trading: #{i+1}')
        fund_to_trading = await fundingWallet.ExecuteTransfer(icp, 0.01, 'fund_to_trade')
        id = fund_to_trading['id']
        state = fund_to_trading['state']
        if state != 'success':
            print(f'ERROR state - {id} - {state}')
        wallet_transfer_kind = fund_to_trading['wallet_transfer_kind']
        if wallet_transfer_kind != 'fund_to_trade':
            print(f'ERROR wallet_transfer_kind - {id} - {wallet_transfer_kind}')

if __name__ == "__main__":
    asyncio.run(main())