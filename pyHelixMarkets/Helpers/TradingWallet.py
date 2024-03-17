import asyncio
import json
from Ordergateway import Ordergateway
from Keymakerfund import Keymakerfund

class TradingWallet:

    _Ordergateway: Ordergateway = None
    _Keymakerfund: Keymakerfund = None

    def __init__(self, ordergateway: Ordergateway):
        self._Ordergateway = ordergateway
        self._Keymakerfund = Keymakerfund()

    def GetBalances(self, asset: str = None):
        balances = self._Ordergateway.TradingWalletBalances
        if balances is None:
            print(f'\nTradingWallet error: empty balances')
            return
        if asset is None:
            return balances
        return float(balances[asset.upper()])
    
    async def WaitUntilBalance(self, asset: str, amount: float) -> bool:
        print(f"\nWaiting for {asset.upper()} {amount} in Trading wallet...", end='')
        while True:
            balance = self.GetBalances(asset=asset)
            if balance is None:
                return False
            if balance >= amount:
                print('done')
                return True
            print('.', flush=True, end='')
            await asyncio.sleep(2)

    def GetTransfers(self, id: str = None, asset: str = None, kind: str = None, start_time: int = None, end_time: int = None) -> list[dict]:
        transfer_history = self._Keymakerfund.TransferHistory(id, asset, start_time, end_time)
        if transfer_history.status_code != 200:
            print(f'\nGetTransfers error: #{transfer_history.status_code} - {transfer_history.text}')
            return
        transfers = json.loads(transfer_history.text)['result'] 
        if kind is not None:
            transfers = [transfer for transfer in transfers if transfer['wallet_transfer_kind'] == kind]
        if id is None:
            return transfers
        return next((transfer for transfer in transfers), None)

    def GetActiveTransfers(self, asset: str = None, kind: str = None, start_time: int = None, end_time: int = None):
        transfers = self.GetTransfers(asset=asset, kind=kind, start_time=start_time, end_time=end_time)
        if not transfers:
            return
        return [active_transfer for active_transfer in transfers if 'state' in transfers and active_transfer['state'] != 'success' and active_transfer['state'] != 'failure']
    
    # asset = HelixTokens
    # direction = 'fund_to_trade' | 'trade_to_fund'
    async def ExecuteTransfer(self, asset: dict, amount: float, direction: str) -> dict:
        transfer = self._Keymakerfund.WalletTransfer(asset['chain'], asset['native_asset'], asset['asset'], amount, direction)
        if transfer.status_code != 200:
            print(f"Transferring error: #{transfer.status_code} - {transfer.text}")
            return
        request_id = json.loads(transfer.text)['rid']
        print(f"\nInitiated {direction} transfer for {asset['asset']} {amount}...id={request_id}")
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
    
    async def NewOrder(self, symbol: str, orderType: str, orderSide: str, timeInForce: str = 'gtc', price: float = None, totalQuantity: float = None, quoteTotalQuantity: float = None, maxSlippage: float = None, clientOrderId: int = None) -> str:
        new_order_clientOrderId = await self._Ordergateway.NewOrder(symbol, orderType, orderSide, timeInForce, price, totalQuantity, quoteTotalQuantity, maxSlippage, clientOrderId)
        if new_order_clientOrderId is None:
            return None
        return new_order_clientOrderId
    
    async def CancelOrder(self, symbol: str, clientOrderId) -> str:
        cancel_order_clientOrderId = await self._Ordergateway.CancelOrder(symbol, clientOrderId)
        if cancel_order_clientOrderId is None:
            return None
        return cancel_order_clientOrderId