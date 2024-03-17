import asyncio
import threading
import json
import websockets
import time
import configparser
from pathlib import Path

class Datagateway:

    _base_url: str = None
    _sequenceNumber: int = 0
    _websocket: websockets.WebSocketClientProtocol = None

    IsDisconnected: threading.Event = None

    Symbols: dict[str, str] = {}

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

        if 'dgw_base_url' not in config['HelixMarkets']:
            print('dgw_base_url not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._base_url = config['HelixMarkets']['dgw_base_url']

    def _get_ts(self) -> int:
        return int(time.time() * 1000000)      # return unix timestamp in microseconds
    
    def _get_next_sequence_number(self) -> int:
        self._sequenceNumber += 1
        return self._sequenceNumber

    async def _handler(self):
        while self.IsDisconnected.is_set() is False:
            try:
                try:
                    message_json = await asyncio.wait_for(self._websocket.recv(), timeout=5)
                except asyncio.TimeoutError:
                    continue
                message = json.loads(message_json)
                if message['msg'] == 'SymbolsReply':
                    self.Symbols = message
                else:
                    print(message)
            except websockets.exceptions.ConnectionClosed:
                print('Datagateway connection closed')
                break
            except Exception as e:
                print(f'Datagateway exception handler: {type(e)}')

    async def _connect(self, connectEvent: threading.Event):
        async with websockets.connect(self._base_url) as websocket:
            self._websocket = websocket
            await self.GetSymbols()
            connectEvent.set()
            await self._handler()

    async def Connect(self) -> bool:
        if self._base_url is None:
            print('Datagateway configuration not set')
            return False
        connectEvent = threading.Event()
        self.IsDisconnected = threading.Event()
        thread = threading.Thread(target=asyncio.run, args=(self._connect(connectEvent),))
        thread.start()
        # sleep to allow for SymbolsReply to be returned
        await asyncio.sleep(1)
        return connectEvent.wait(timeout=5)
    
    def Close(self):
        self.IsDisconnected.set()

    async def GetSymbols(self, pattern: str = '*'):
        if self.IsDisconnected.is_set():
            print('Datagateway not connected')
            return
        symbols_request = {
            'msg': 'Symbols',
            'ts': self._get_ts(),
            'seqn': self._get_next_sequence_number(),
            'pattern': pattern
        }
        await self._websocket.send(json.dumps(symbols_request))
