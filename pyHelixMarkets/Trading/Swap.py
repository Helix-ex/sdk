import asyncio
import json
from Ordergateway import Ordergateway
from Color import Color

class Swap:

    _Ordergateway: Ordergateway = None
    _executions: list[dict] = None

    def __init__(self, ordergateway: Ordergateway):
        self._Ordergateway = ordergateway

    async def ExecuteSwap(self, asset: str, side: str, amount: float) -> list[dict]:
        print(f'\n{Color.GREEN}Executing swap...{Color.END}')
        clientOrderId = await self._Ordergateway.NewOrder(asset, 'market', side, 'gtc', totalQuantity=amount)
        order_stop = False
        self._executions = []
        while not order_stop:
            await asyncio.sleep(2)
            requests = self._Ordergateway.RequestManager[clientOrderId]
            for request in requests:
                msg = request['msg']
                if msg == 'Error':
                    formatted_request = json.dumps(request, indent=2)
                    print(f"{Color.RED}Order error: {formatted_request}{Color.END}")
                    self._executions.append(request)
                    order_stop = True
                    break
                if 'status' not in request:
                    # ignore non-status messages: NewOrder, CancelOrder, ReplaceOrder
                    continue
                status = request['status']
                if msg == 'OrderTrade' and status == 'filled':
                    print(f"Order filled: {request['side'].upper()} {request['symbol']} {request['execQty']} @ {request['tradePrice']}")
                    self._executions.append(request)
                    order_stop = True
                    break
                elif status == 'replaced':
                    formatted_request = json.dumps(request, indent=2)
                    print(f"Order replaced: {formatted_request}")
                    self._executions.append(request)
                    order_stop = True
                    break
                elif status == 'cancelled':
                    formatted_request = json.dumps(request, indent=2)
                    print(f"Order cancelled: {formatted_request}")
                    self._executions.append(request)
                    order_stop = True
                    break
                elif status == 'rejected':
                    formatted_request = json.dumps(request, indent=2)
                    print(f"{Color.RED}Order rejected: {formatted_request}{Color.END}")
                    self._executions.append(request)
                    order_stop = True
                    break
        print(f'{Color.GREEN}Swap completed{Color.END}')
        return self._executions

async def main():
    ordergateway = Ordergateway()
    if await ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        twap = Swap(ordergateway)
        await twap.ExecuteSwap('HTICP/USDC', 'sell', 1)
    finally:
        ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())