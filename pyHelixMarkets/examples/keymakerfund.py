import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Keymakerfund import Keymakerfund

async def main():
    keymakerfund = Keymakerfund()

    chainAssets = keymakerfund.ChainAssets()
    helixTokens = json.loads(chainAssets.text)['chain_assets']
    helixTokens_formatted = json.dumps(helixTokens, indent=2)
    print(f"\nChain assets:\n{helixTokens_formatted}")

    feeEstimate = keymakerfund.FeeEstimates()
    feeEstimate_obj = json.loads(feeEstimate.text)
    feeEstimate_formatted = json.dumps(feeEstimate_obj, indent=2)
    print(f"\nFee estimates:\n{feeEstimate_formatted}")

    feeEstimate_json = json.loads(feeEstimate.text)
    assets = feeEstimate_json['assets']
    print(f"\nFee estimates:")
    for asset in assets:
        print(f"Asset: {asset['asset']} service fee: {asset['service_fee']} chain fee: {asset['chain_fee']} service fee (usd): {asset['service_fee_usd']}")

    fundingWalletBalance = keymakerfund.FundingWalletBalances()
    fundingWalletBalance_obj = json.loads(fundingWalletBalance.text)
    fundingWalletBalance_formatted = json.dumps(fundingWalletBalance_obj, indent=2)
    print(f"\nFunding wallet balances:\n{fundingWalletBalance_formatted}")

    transferHistory = keymakerfund.TransferHistory()
    transferHistory_obj = json.loads(transferHistory.text)
    transferHistory_formatted = json.dumps(transferHistory_obj, indent=2)
    print(f"\nTransfer history:\n{transferHistory_formatted}")

    transfer_id = keymakerfund.TransferHistory(id='d92456e5-8421-4db3-9e0a-d2fe23f08c61')
    transfer_id_obj = json.loads(transfer_id.text)
    transfer_id_formatted = json.dumps(transfer_id_obj, indent=2)
    print(f"\nTransfer id:\n{transfer_id_formatted}")

if __name__ == "__main__":
    asyncio.run(main())