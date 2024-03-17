import json
from Keymakerfund import Keymakerfund

_QtyNumDigits = {
    "btc": 6,
    "eth": 5,
    "usdc": 2,
    "usdt": 2,
    "icp": 2,
    "ckbtc": 6,
    "cketh": 5
}

_keymakerfund = Keymakerfund()
_chain_assets_json = _keymakerfund.ChainAssets()
_chain_assets = json.loads(_chain_assets_json.text)['chain_assets']

# create HelixTokens dictionary
HelixTokens = {}
for token in _chain_assets:
    if token['asset'] in _QtyNumDigits:
        token['qty_num_digits'] = _QtyNumDigits[token['asset']]
    HelixTokens[token['asset']] = token

def get_base_currency(symbol: str) -> str:
    lsymbol = symbol.lower()
    # check if beginnging of symbol is a token
    for token in HelixTokens:
        if lsymbol.startswith(token):
            return token
    return

def get_quote_currency(symbol: str) -> str:
    lsymbol = symbol.lower()
    # check if end of symbol is a token
    for token in HelixTokens:
        if lsymbol.endswith(token):
            return token
    return