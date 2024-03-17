import requests
import configparser
from pathlib import Path
from Signing import Signing

class FundingProxy:

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

        if 'fnp_base_url' not in config['HelixMarkets']:
            print('fnp_base_url not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._base_url = config['HelixMarkets']['fnp_base_url']
        if 'huid' not in config['HelixMarkets']:
            print('huid not found in [HelixMarkets] section of helix_secret.cfg')
            return
        self._huid = int(config['HelixMarkets']['huid'])
        if 'fnp_api_token' not in config['HelixMarkets']:
            print('fnp_api_token not found in [HelixMarkets] section of helix_secret.cfg')
            return
        api_token: str = config['HelixMarkets']['fnp_api_token']

        self._Signing = Signing(self._huid, api_token)

    def User(self, huid: int = None, principal_id: str = None) -> requests.Response:
        path: str = '/user'
        method: str = 'GET'
        payload = None
        auth_headers = self._Signing.GetAuthHeaders(path, method, payload)
        if principal_id is not None:
            path += f'?principal_id={principal_id}'
        elif huid is not None:
            path += f'?huid={huid}'
        else:
            path += f'?huid={self._huid}'
        url = self._base_url + path
        return requests.get(url, headers=auth_headers)