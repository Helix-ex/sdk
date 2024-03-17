import requests
import json
import configparser
from pathlib import Path
from Signing import Signing

class Keymakerfund:

    _base_url: str = None
    _huid: int = None
    _Signing: Signing = None

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

        if 'kmf_base_url' not in config['HelixMarkets']:
            print('kmf_base_url not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._base_url = config['HelixMarkets']['kmf_base_url']
        if 'huid' not in config['HelixMarkets']:
            print('huid not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._huid = int(config['HelixMarkets']['huid'])
        if 'kmf_api_token' not in config['HelixMarkets']:
            print('kmf_api_token not found in [HelixMarkets] section of helix_secret.cfg')
            return
        api_token: str = config['HelixMarkets']['kmf_api_token']

        self._Signing = Signing(self._huid, api_token)

    def ChainAssets(self) -> requests.Response:
        path: str = '/chain_assets'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        url = self._base_url + path
        return requests.get(url, headers=auth_headers)

    def FeeEstimates(self) -> requests.Response:
        path: str = '/fee_estimates'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        url = self._base_url + path
        return requests.get(url, headers=auth_headers)
    
    # this gets all the deposits, withdraws and transfers
    # however, doesn't returh the state
    # replaced by TransferHistory()
    # def FundingHistory(self, id: str = None) -> requests.Response:
    #     path: str = '/funding'
    #     method: str = 'GET'
    #     payload = None
    #     auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
    #     url = self._base_url + path + f'?huid={self._huid}'
    #     if id is not None:
    #         url += '&id=' + id
    #     return requests.get(url, headers=auth_headers)

    # this gets only withdraws and transfers
    # replaced by TransferHistory()
    # def WalletTransfers(self, id: str = None) -> requests.Response:
    #     path: str = '/wallet_transfer'
    #     method: str = 'GET'
    #     payload = None
    #     auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
    #     url = self._base_url + path + f'?huid={self._huid}'
    #     if id is not None:
    #         url += '&id=' + id
    #     return requests.get(url, headers=auth_headers)

    def FundingWalletBalances(self) -> requests.Response:
        path: str = '/balances/funding' + f'/{self._huid}'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        url = self._base_url + path
        return requests.get(url, headers=auth_headers)

    # this gets all the deposits, withdraws and transfers
    # this is the best method to use
    def TransferHistory(self, id: str = None, asset: str = None, start_time: int = None, end_time: int = None) -> requests.Response:
        path: str = '/sapi/v1/asset/transfer'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        url = self._base_url + path + f'?huid={self._huid}'
        if asset is not None:
            url += '&asset=' + asset
        if id is not None:
            url += '&id=' + id
        if start_time is not None:
            url += '&start_time=' + start_time
        if end_time is not None:
            url += '&end_time=' + end_time
        return requests.get(url, headers=auth_headers)

    def WalletTransfer(self, chain: str, native_asset: str, asset: str, amount: float, direction: str, external_label: str = None, speed: str = None) -> requests.Response:
        path: str = '/wallet_transfer'
        method: str = 'POST'
        payload = {
            'huid': str(self._huid),
            'chain': chain,
            'native_asset': native_asset,
            'asset': asset,
            'amount': str(amount),
            'direction': direction,
        }
        if external_label is not None:
            payload.update({'external_label': external_label})
        if speed is not None:
            payload.update({'speed': speed})
        payload_json = json.dumps(payload)
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload_json)
        url = self._base_url + path
        return requests.post(url, headers=auth_headers, data=payload_json)
    
    def TransferStatus(self, id: str) -> requests.Response:
        path: str = '/wallet_transfer_status'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        url = self._base_url + path + f'/{id}'
        return requests.get(url, headers=auth_headers)
