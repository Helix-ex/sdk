import asyncio
import threading
import json
import websockets
import time
import random
import configparser
from pathlib import Path

class Ordergateway:

    _base_url: str = None
    _huid: int = None
    _api_token: str = None
    _account: str = None
    _sequenceNumber: int = 0
    _websocket: websockets.WebSocketClientProtocol = None

    IsAuthorized: threading.Event = None
    IsDisconnected: threading.Event = None

    TradingWalletBalances: dict[str, float] = {}
    RequestManager: dict[int, list] = {}

    def __init__(self):
        config_file = Path('helix_secret.cfg')
        if config_file.is_file() == False:
            print('helix_secret.cfg not found')
            return
        config = configparser.ConfigParser()
        config.read('helix_secret.cfg')
        config_sections = config.sections()
        if 'HelixMarkets' not in config_sections:
            print('HelixMarkets section not found in helix_secret.cfg')
            return

        if 'ogw_base_url' not in config['HelixMarkets']:
            print('ogw_base_url not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._base_url = config['HelixMarkets']['ogw_base_url']
        if 'huid' not in config['HelixMarkets']:
            print('huid not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._huid = int(config['HelixMarkets']['huid'])
        if 'ogw_api_token' not in config['HelixMarkets']:
            print('ogw_api_token not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._api_token = config['HelixMarkets']['ogw_api_token']
        if 'ogw_account' not in config['HelixMarkets']:
            print('ogw_account not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._account = config['HelixMarkets']['ogw_account']
        self._sequenceNumber = 0

    def _get_ts(self) -> int:
        return int(time.time() * 1000000)      # return unix timestamp in microseconds
    
    def _get_next_sequence_number(self) -> int:
        self._sequenceNumber += 1
        return self._sequenceNumber

    async def _handler(self):
        while self.IsDisconnected.is_set() is False:
            try:
                try:
                    # timeout after 5 seconds as no message and see if IsDisconnected is set
                    message_json = await asyncio.wait_for(self._websocket.recv(), timeout=5)
                except asyncio.TimeoutError:
                    continue
                message = json.loads(message_json)
                if message['msg'] == 'OrderUpdate':
                    self.RequestManager[message['clientOrderId']].append(message)
                elif message['msg'] == 'OrderTrade':
                    self.RequestManager[message['clientOrderId']].append(message)
                elif message['msg'] == 'AssetBalanceQueryReply':
                    for account in message['balances']:
                        self.TradingWalletBalances.update({account['asset']: account['total']})
                elif message['msg'] == 'AssetBalance':
                    self.TradingWalletBalances.update({message['asset']: message['total']})
                elif message['msg'] == 'OrderQueryReply':
                    pass
                elif message['msg'] == 'TradeQueryReply':
                    pass
                elif message['msg'] == 'NewOrderStatus':
                    if message['status'] == 'rejected':
                        print(f"Ordergateway new order rejected: {message['errCode']} - {message['errMessage']}")
                        return
                    self.RequestManager[message['clientOrderId']].append(message)
                elif message['msg'] == 'OrderReplaceStatus':
                    if message['status'] == 'rejected':
                        print(f"Ordergateway replace order rejected: {message['errCode']} - {message['errMessage']}")
                        return
                    self.RequestManager[message['origClientOrderId']].append(message)
                    self.RequestManager[message['clientOrderId']].append(message)
                elif message['msg'] == 'OrderCancelStatus':
                    if message['status'] == 'rejected':
                        print(f"Ordergateway cancel order rejected: {message['errCode']} - {message['errMessage']}")
                        return
                    self.RequestManager[message['clientOrderId']].append(message)
                elif message['msg'] == 'LogonReply':
                    if 'errCode' in message:
                        print(f"Ordergateway logon error: #{message['errCode']} - {message['errMessage']}")
                        continue
                    print(f"Ordergateway user {message['clientId']}/{message['account']} authorized")
                    self.IsAuthorized.set()
                elif message['msg'] == 'Error':
                    # find the original request by refSeqn and refMsg and append the error message
                    refSeqn = int(message['refSeqn'])
                    refMsg = message['refMsg']
                    match = False
                    for clientOrderId in self.RequestManager:
                        for request in self.RequestManager[clientOrderId]:
                            if request['seqn'] == refSeqn and request['msg'] == refMsg:
                                self.RequestManager[clientOrderId].append(message)
                                match = True
                                break
                        if match:
                            break
                else:
                    print(message)
            except websockets.exceptions.ConnectionClosed:
                print('Ordergateway connection closed')
                break
            except KeyError:
                # request not in RequestManager. could be from UI or other source
                pass
            except Exception as e:
                print(f'Ordergateway exception handler: {type(e)}')

    async def _logon(self):
        logon_request = {
            'msg': 'LogonRequest',
            'ts': self._get_ts(),
            'seqn': self._get_next_sequence_number(),
            'clientId': self._huid,
            'token': self._api_token,
            'account': self._account
        }
        await self._websocket.send(json.dumps(logon_request))

    def GetClientOrderId(self) -> int:
        return random.getrandbits(58)

    async def _connect(self):
        async with websockets.connect(self._base_url) as websocket:
            self._websocket = websocket
            await self._logon()
            await self._handler()

    async def Connect(self) -> bool:
        if self._base_url is None or \
            self._huid is None or \
            self._api_token is None or \
            self._account is None:
            print('Ordergateway configuration not set')
            return False
        self.IsAuthorized = threading.Event()
        self.IsDisconnected = threading.Event()
        thread = threading.Thread(target=asyncio.run, args=(self._connect(),))
        thread.start()
        # sleep to allow for AssetBalanceQueryReply to be returned
        await asyncio.sleep(1)
        return self.IsAuthorized.wait(timeout=5)

    def Close(self):
        self.IsDisconnected.set()

    # orderType: market | limit
    # orderSide: buy | sell
    # timeInForce: gtc | ioc | fok | gtx
    async def NewOrder(self, symbol: str, orderType: str, orderSide: str, timeInForce: str = 'gtc', price: float = None, totalQuantity: float = None, quoteTotalQuantity: float = None, maxSlippage: float = None, clientOrderId: int = None) -> str:
        if self.IsDisconnected.is_set():
            print('Ordergateway not connected')
            return None
        if clientOrderId is None:
            clientOrderId = self.GetClientOrderId()
        neworder_request = {
            'msg': 'NewOrder',
            'ts': self._get_ts(),
            'seqn': self._get_next_sequence_number(),
            'symbol': symbol,
            'type': orderType,
            'side': orderSide,
            'tif': timeInForce,
            'clientOrderId': clientOrderId
        }
        if price is not None:
            neworder_request.update({'price': str(price)})
        if totalQuantity is not None:
            neworder_request.update({'totalQty': str(totalQuantity)})
        if quoteTotalQuantity is not None:
            neworder_request.update({'quoteTotalQty': str(quoteTotalQuantity)})
        if maxSlippage is not None:
            neworder_request.update({'maxSlippage': maxSlippage})
        self.RequestManager[clientOrderId] = []
        self.RequestManager[clientOrderId].append(neworder_request)
        await self._websocket.send(json.dumps(neworder_request))
        return clientOrderId

    # replace existing order = origClientOrderId, with
    # new order = clientOrderId changing price or totalQuantity
    async def ReplaceOrder(self, symbol: str, origClientOrderId: int, price: float = None, totalQuantity: float = None, clientOrderId: int = None) -> str:
        if self.IsDisconnected.is_set():
            print('Ordergateway not connected')
            return None
        if clientOrderId is None:
            clientOrderId = self.GetClientOrderId()
        replaceorder_request = {
            'msg': 'ReplaceOrder',
            'ts': self._get_ts(),
            'seqn': self._get_next_sequence_number(),
            'symbol': symbol,
            'clientOrderId': clientOrderId,
            'origClientOrderId': origClientOrderId
        }
        if price is not None:
            replaceorder_request.update({'price': str(price)})
        if totalQuantity is not None:
            replaceorder_request.update({'totalQty': str(totalQuantity)})
        self.RequestManager[origClientOrderId].append(replaceorder_request)
        self.RequestManager[clientOrderId] = []
        self.RequestManager[clientOrderId].append(replaceorder_request)
        await self._websocket.send(json.dumps(replaceorder_request))
        return clientOrderId

    async def CancelOrder(self, symbol: str, clientOrderId) -> str:
        if self.IsDisconnected.is_set():
            print('Ordergateway not connected')
            return None
        cancelorder_request = {
            'msg': 'CancelOrder',
            'ts': self._get_ts(),
            'seqn': self._get_next_sequence_number(),
            'symbol': symbol,
            'clientOrderId': clientOrderId
        }
        self.RequestManager[clientOrderId].append(cancelorder_request)
        await self._websocket.send(json.dumps(cancelorder_request))
        return clientOrderId