import asyncio
import json
from Ordergateway import Ordergateway
from HelixTokens import HelixTokens, get_base_currency
from Color import Color

class Twap:

    _Ordergateway: Ordergateway = None
    _executions: list[dict] = None

    def __init__(self, ordergateway: Ordergateway):
        self._Ordergateway = ordergateway

    # twap_duration in hours
    # twap_num_intervals is the number of intervals to divide the twap_duration
    async def ExecuteTwap(self, asset: str, side: str, amount: float, twap_duration: float, twap_num_intervals: int) -> list[dict]:
        twap_duration_sec: int = int(twap_duration * 3600)
        interval_duration_sec: int = int(twap_duration_sec / twap_num_intervals)
        base_currency: str = get_base_currency(asset.lower())
        if not base_currency:
            print(f"Unsupported base asset: {asset}")
            return
        qty_num_digits: int = int(HelixTokens[base_currency]['qty_num_digits'])
        interval_amount: float = round(float(amount / twap_num_intervals), qty_num_digits)

        print(f"\nRunning Twap strategy for {twap_duration_sec:,} secs with {twap_num_intervals:,} intervals of {interval_duration_sec:,} secs each")
        print(f'{side} {asset} for total amount {amount:,} with each interval amount {interval_amount:,}')

        self._executions = []
        for interval in range(twap_num_intervals):
            asyncio.create_task(self._execute_interval(interval, twap_num_intervals, asset, side, interval_amount))
            await asyncio.sleep(interval_duration_sec)

        return self._executions

    async def _execute_interval(self, current_interval: int, twap_num_intervals: int, asset: str, side: str, interval_amount: float):
        print(f'\n{Color.GREEN}Executing interval {Color.MAGENTA}{current_interval+1}{Color.GREEN}/{twap_num_intervals}...{Color.END}')
        clientOrderId = await self._Ordergateway.NewOrder(asset, 'market', side, 'gtc', totalQuantity=interval_amount)
        order_stop = False
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
        print(f'{Color.GREEN}Interval {Color.MAGENTA}{current_interval+1}{Color.GREEN}/{twap_num_intervals} completed{Color.END}')

async def main():
    ordergateway = Ordergateway()
    if await ordergateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        twap = Twap(ordergateway)
        # 0.0167 hours = 1 minute
        await twap.ExecuteTwap('HTICP/USDC', 'sell', 10, 0.0167, 10)
    finally:
        ordergateway.Close()

if __name__ == "__main__":
    asyncio.run(main())