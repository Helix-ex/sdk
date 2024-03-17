import json
from FundingProxy import FundingProxy

# helper class to get user data
class User:

    _FundingProxy: FundingProxy = None

    def __init__(self):
        self._FundingProxy = FundingProxy()

    def Get(self) -> str:
        user = self._FundingProxy.User()
        if user.status_code != 200:
            print(f'\nUser error: #{user.status_code} - {user.text}')
            return
        return user.text
    
    def GetHuid(self) -> str:
        user = self.Get()
        if not user:
            return
        return json.loads(user)['data']['huid']
    
    def GetDepositAddresses(self, chain: str = None) -> list[dict]:
        user = self.Get()
        if not user:
            return
        keys_addresses = json.loads(user)['data']['keys_addresses']
        if chain is not None:
            return [address for address in keys_addresses if address['chain'] == chain]
        return keys_addresses

    def GetDepositAddress(self, chain: str):
        user = self.Get()
        if not user:
            return
        keys_addresses = json.loads(user)['data']['keys_addresses']
        for address in keys_addresses:
            if address['chain'] == chain:
                if chain == 'icp':
                    return [address['address'], address['icp_account_id']]
                else:
                    return address['address']
                
    def GetExternalAddresses(self, chain: str = None) -> list[dict]:
        user = self.Get()
        if not user:
            return
        external_addresses = json.loads(user)['data']['external_addresses']
        if chain is not None:
            return [address for address in external_addresses if address['chain'] == chain]
        return external_addresses
    
    def GetExternalAddress(self, label: str, chain: str = None) -> dict:
        external_addresses = self.GetExternalAddresses(chain)
        if not external_addresses:
            return
        for address in external_addresses:
            if address['label'] == label:
                return address