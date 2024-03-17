import asyncio
import json
from HelixTokens import HelixTokens
from Keymakerfund import Keymakerfund
from Helpers.User import User

# helper class for Funding Wallet operations
class FundingWallet:

    _Keymakerfund: Keymakerfund = None
    _User: User = None

    def __init__(self):
        self._Keymakerfund = Keymakerfund()
        self._User = User()

    def GetBalances(self, asset: str = None):
        balances = self._Keymakerfund.FundingWalletBalances()
        if balances.status_code != 200:
            print(f'\nFundingWallet error: #{balances.status_code} - {balances.text}')
            return
        balances = json.loads(balances.text)['result']
        if asset is None:
            return balances
        return next((float(balance['amount']) for balance in balances if balance['asset'] == asset.lower()), None)
    
    async def WaitUntilBalance(self, asset: str, amount: float) -> bool:
        balance = self.GetBalances(asset=asset)
        if not balance:
            return False
        # if already has enough balance, no need to wait for deposit
        if balance >= amount:
            return True
        
        chain = HelixTokens[asset]['chain']
        qty_num_digits = HelixTokens[asset]['qty_num_digits']
        u_asset = asset.upper()
        deposit_address = self._User.GetDepositAddress(chain)
        needed_deposit_amount = round(amount - balance, qty_num_digits)
        print(f"\nPlease deposit at least {u_asset} {needed_deposit_amount:,} to {deposit_address}")
        print(f"Waiting for balance of {u_asset} {amount:,} in Funding wallet...", end='')

        while True:
            balance = self.GetBalances(asset=asset)
            if balance is None:
                return False
            if balance >= amount:
                print('done')
                return True
            print('.', flush=True, end='')
            await asyncio.sleep(2)

    # kind:
    #   deposit = external_to_fund 
    #   transfer = fund_to_trade | trade_to_fund
    #   withdraw = fund_to_external
    def GetTransfers(self, id: str = None, asset: str = None, kind: str = None, start_time: int = None, end_time: int = None):
        transfer_history = self._Keymakerfund.TransferHistory(id, asset, start_time, end_time)
        if transfer_history.status_code != 200:
            print(f'\nGetTransfers error: #{transfer_history.status_code} - {transfer_history.text}')
            return
        transfers = json.loads(transfer_history.text)['result']
        if kind is not None:
            transfers = [transfer for transfer in transfers if 'wallet_transfer_kind' in transfer and transfer['wallet_transfer_kind'] == kind]
        if id is None:
            return transfers        
        return next((transfer for transfer in transfers), None)
    
    def GetActiveTransfers(self, asset: str = None, kind: str = None, start_time: int = None, end_time: int = None) -> list[dict]:
        transfers = self.GetTransfers(asset=asset, kind=kind, start_time=start_time, end_time=end_time)
        if not transfers:
            return
        return [active_transfer for active_transfer in transfers if 'state' in transfers and active_transfer['state'] != 'success' and active_transfer['state'] != 'failure']
    
    # asset = HelixTokens
    # direction = 'fund_to_trade' | 'trade_to_fund' | 'fund_to_external'
    # external_label = whitelabelled external address
    async def ExecuteTransfer(self, asset: dict, amount: float, direction: str, external_label: str = None) -> dict:
        if external_label is not None:
            external_address = self._User.GetExternalAddress(external_label, asset['chain'])
            if not external_address:
                print(f'\nExternal address {external_label} not found...')
                return
        transfer = self._Keymakerfund.WalletTransfer(asset['chain'], asset['native_asset'], asset['asset'], amount, direction, external_label)
        if transfer.status_code != 200:
            print(f"Transferring error: #{transfer.status_code} - {transfer.text}")
            return
        request_id = json.loads(transfer.text)['rid']
        print(f"\nInitiated {direction} transfer for {asset['asset']} {amount}...id={request_id}")
        if external_label is not None:
            print(f"External address: {external_address['label']} - {external_address['address']}")
        prev_status = ''
        while True:
            transfer_status = self._Keymakerfund.TransferStatus(request_id)
            if transfer_status.status_code != 200:
                print(f"\nTransfer status error: #{transfer_status.status_code} - {transfer_status.text}")
                return
            status = json.loads(transfer_status.text)['status']
            if status != prev_status:
                print(status)
                prev_status = status
            if status == 'failure':
                break
            elif status == 'success':
                break
            await asyncio.sleep(2)
        return self.GetTransfers(id=request_id)

    # asset = HelixTokens
    def GetFeeEstimates(self, asset: dict = None):
        fee_estimates = self._Keymakerfund.FeeEstimates()
        if fee_estimates.status_code != 200:
            print(f'\nFee estimate error: #{fee_estimates.status_code} - {fee_estimates.text}')
            return
        assets = json.loads(fee_estimates.text)['assets']
        if asset is None:
            return assets
        return next((fee for fee in assets if 'chain' in fee and fee['chain'] == asset['chain'] and 'asset' in fee and fee['asset'] == asset['asset']), None)

    def TransferStatus(self, id: str) -> str:
        transfer_status = self._Keymakerfund.TransferStatus(id)
        if transfer_status.status_code != 200:
            print(f'\TransferStatus error: #{transfer_status.status_code} - {transfer_status.text}')
            return
        return transfer_status.text
