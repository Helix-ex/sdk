# pyHelixMarkets
python sdk for funding proxy, keymaker fund, datagateway and ordergateway

Installation:

python -m venv .venv        # to create virtual environment in .venv directory
source .venv/bin/activate   # to activate .venv environment

pip install -r requirements.txt # to install required packages

Example programs:

fundingwallet and tradingwallet demostrates the helper classes which provide the high-level operations

examples/fundingwallet.py
examples/tradingwallet.py

the rest are more lower-level operations to each specific service:

examples/fundingproxy.py
examples/keymakerfund.py
examples/datagateway.py

You will need to have a **helix_secret.cfg** configuration file which has all your secrets.

Example **helix_secret.cfg** or rename helix_example.cfg

[HelixMarkets]<br />
# replace with your huid<br />
huid = 314207<br />
fnp_base_url = https://fnp.staging.apt.st<br />
# replace with your "Secret Key" from API Managment<br />
fnp_api_token = sajfisdajoi...asdifjdsaijosdfjio<br />
kmf_base_url = https://kmf.staging.apt.st<br />
# same as fnp_api_token<br />
kmf_api_token = sajfisdajoi...asdifjdsaijosdfjio<br />
ogw_base_url = wss://ogw.staging.apt.st<br />
# replace with your "Websocket Authentication Token" from API Managment<br />
ogw_api_token = adsfidjo...usadfjhfsaduih<br />
ogw_account = default<br />
dgw_base_url = wss://dgw.staging.apt.st<br />

To use Docker:

docker build -t pyhelixmarkets .<br />
docker run -it pyhelixmarkets<br />
root@b1756e0e7cbe:/app# python3 main.py<br />
root@b1756e0e7cbe:/app# python3 helix.py<br />
root@b1756e0e7cbe:/app# python3 transfer.py<br />
