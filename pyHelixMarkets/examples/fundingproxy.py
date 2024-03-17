import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from FundingProxy import FundingProxy

async def main():
    fundingproxy = FundingProxy()

    user = fundingproxy.User()
    user_data = json.loads(user.text)
    user_data_formatted = json.dumps(user_data, indent=2)
    print(f"\nUser:\n{user_data_formatted}")

if __name__ == "__main__":
    asyncio.run(main())