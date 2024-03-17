import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Helpers.User import User

async def main():
    user = User()

    # return specific user data
    print(f'\nHuid: {user.GetHuid()}')
    print(f'BTC deposit address: {user.GetDepositAddress("btc")}')
    print(f'ETH deposit address: 0x{user.GetDepositAddress("eth")}')
    print(f'ICP deposit address (principal id): {user.GetDepositAddress("icp")[0]}')
    print(f'ICP deposit address (account id): {user.GetDepositAddress("icp")[1]}')

    # returns everything
    user_data = json.loads(user.Get())
    user_data_formatted = json.dumps(user_data, indent=2)
    print(f'\nUser data:\n{user_data_formatted}')

    # returns all deposit addresses
    deposit_addresses_formatted = json.dumps(user.GetDepositAddresses(), indent=2)
    print(f'\nDeposit addresses:\n{deposit_addresses_formatted}')
    # returns all registered external addresses
    external_addresses_formatted = json.dumps(user.GetExternalAddresses(), indent=2)
    print(f'\nExternal addresses:\n{external_addresses_formatted}')

if __name__ == "__main__":
    asyncio.run(main())