import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Datagateway import Datagateway

async def main():
    datagateway = Datagateway()
    if await datagateway.Connect() is False:
        print('Error connecting to Ordergateway')
        return
    try:
        await datagateway.Connect()

        symbols = datagateway.Symbols
        symbols_formatted = json.dumps(symbols, indent=2)
        print(f"\nSymbols:\n{symbols_formatted}")
    finally:
        datagateway.Close()

if __name__ == "__main__":
    asyncio.run(main())