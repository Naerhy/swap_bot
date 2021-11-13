from web3 import Web3
import json
import sys
import time

# multi file with class in it ?
# add text color ?
# use .env to store addresses + keys
# use another class to store check/verify functions !
    # better => use inheritance: BotControl (parent) => Bot (child)
# define setters/getters ?
# security check if user_args slippage/amount == letters ?
# check return values of some functions => check errors

class Bot:
    def __init__(self, user_address, private_key):
        self.user_address = user_address
        self.private_key = private_key
        self.list_providers = self.get_list_providers()
        self.list_routers = self.get_list_routers()
        self.get_user_args()
        self.launch_bot()
        self.prepare_trade()

    def get_list_providers(self):
        list_providers = {
            "avax": "https://api.avax.network/ext/bc/C/rpc",
            "bsc": "https://bsc-dataseed1.defibit.io",
            "eth": "https://rpc.flashbots.net",
            "ftm": "https://rpc.ftm.tools",
            "polygon": "https://polygon-rpc.com"
        }
        return list_providers

    def get_list_routers(self):
        list_routers = {
            "apeswap": [self.list_providers["bsc"], ""],
            "pancakeswap": [self.list_providers["bsc"] ,"0x10ED43C718714eb63d5aA57B78B54704E256024E"],
            "pangolin": [self.list_providers["avax"] ,""],
            "quickswap": [self.list_providers["polygon"] ,""],
            "spiritswap": [self.list_providers["ftm"] ,""],
            "spookyswap": [self.list_providers["ftm"] ,"0xF491e7B69E4244ad4002BC14e878a34207E38c29"],
            "sushiswap": [self.list_providers["eth"] ,""],
            "traderjoe": [self.list_providers["avax"] ,""],
            "uniswap": [self.list_providers["eth"] ,"0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"]
        }
        return list_routers

    def launch_bot(self):
        self.web3 = Web3(Web3.HTTPProvider(self.list_routers[self.user_args[0]][0]))
        if self.web3.isConnected() == False:
            sys.exit("Error: bot was unable to connect to the provider!")
        print("Success: bot is now connected to the provider.")
        self.router = self.web3.eth.contract(address=self.list_routers[self.user_args[0]][1], abi=convert_json("abi/uniswap_router_v2.json"))
        print("Success: bot is now connected to the router.")
    
    def get_user_args(self):
        self.user_args = input("Required information: [ROUTER] [TOKEN ADDRESS] [BUY AMOUNT] [SLIPPAGE]\n").split()
        if len(self.user_args) != 4:
            sys.exit("Error: wrong number of arguments!")
        if self.check_user_args() == False:
            sys.exit("Error: invalid arguments!")

    def check_user_args(self):
        if self.is_valid_router() == False:
            return False
        if self.is_valid_address() == False:
            return False
        if self.is_valid_uint(int(self.user_args[2])) == False:
            return False
        if self.is_valid_uint(int(self.user_args[3])) == False:
            return False
        return True

    def is_valid_router(self):
        for x in self.list_routers:
            if x == self.user_args[0]:
                return True
        return False

    def is_valid_address(self):
        if Web3.isAddress(self.user_args[1]):
            self.user_args[1] = Web3.toChecksumAddress(self.user_args[1])
            return True
        return False
    
    def is_valid_uint(self, nb):
        if nb < 0 or nb > 2 ** 256 - 1:
            return False
        return True
    
    def prepare_trade(self):
        # check if correctly instantied:
        wtoken = self.web3.eth.contract(address=self.router.functions.WETH().call(), abi=convert_json("abi/erc20.json"))

        buy_amount = int(self.user_args[2]) * 10 ** wtoken.functions.decimals().call()

        if wtoken.address == self.user_args[1]:
            sys.exit("Error: you can't swap the same token!")
        if wtoken.functions.balanceOf(self.user_address).call() < buy_amount:
            sys.exit("Error: you don't have enough wrapped tokens!")
        if wtoken.functions.allowance(self.user_address, self.router.address).call() < buy_amount:
            sys.exit("Error: you didn't approve your wrapped tokens to the router!")
        
        path = [wtoken.address, self.user_args[1]]
        # check if pair exists:
        min_received_tokens = self.router.functions.getAmountsOut(buy_amount, path).call()[1] / 100 * (100 - int(self.user_args[3])) # find better calculation?

        user_tx = {
            "from": self.user_address,
            #"gas": 1000000,
            #"gasPrice": 5000000000,
            "nonce": self.web3.eth.getTransactionCount(self.user_address)
        }

        buy_tx = self.router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(buy_amount, int(min_received_tokens), path, self.user_address, int(time.time() + 300)).buildTransaction(user_tx)
        signed_buy_tx = self.web3.eth.account.sign_transaction(buy_tx, private_key=self.private_key)
        print(self.web3.eth.send_raw_transaction(signed_buy_tx.rawTransaction))
        # success message + link to the tx in explorer
        # safe exit

# add to BotControl class
def convert_json(file):
    with open(file) as f:
        return (json.load(f))

#def get_user_tx(user_address):
#    user_tx = {
#        "from": user_address,
#        "gas": 1000000,
#        "gasPrice": 5000000000,
#        "nonce": w3bsc.eth.getTransactionCount(user_address)
#    }
#    return user_tx

def main():
    user_address = ""
    private_key = ""
    bot = Bot(user_address, private_key)

    # check liquidity amount => loop if not enough (= liquidity hasn't been added yet)
    # call swap

if __name__ == "__main__":
    main()