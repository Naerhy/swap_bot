# pip install web3
# pip install python-dotenv

from web3 import Web3
from dotenv import dotenv_values
import json
import re
import sys
import time

# reorganize the code with better classes + inheritance 
# define setters/getters ?
# check return values of some functions => check errors
# find a way to determine gas price depending of blockchain

class Colors:
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    STOP = "\033[0m"
    YELLOW = "\033[33m"

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

    def get_list_routers(self): # get_list_dex ?
        # provider - router - factory
        list_routers = {
            "apeswap": [self.list_providers["bsc"], "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7", "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6"],
            "pancakeswap": [self.list_providers["bsc"], "0x10ED43C718714eb63d5aA57B78B54704E256024E", "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"],
            "pangolin": [self.list_providers["avax"], "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106", "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"],
            "quickswap": [self.list_providers["polygon"], "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"],
            "spiritswap": [self.list_providers["ftm"], "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52", "0xEF45d134b73241eDa7703fa787148D9C9F4950b0"],
            "spookyswap": [self.list_providers["ftm"], "0xF491e7B69E4244ad4002BC14e878a34207E38c29", "0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3"],
            "sushiswap": [self.list_providers["eth"], "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"],
            "traderjoe": [self.list_providers["avax"], "0x60aE616a2155Ee3d9A68541Ba4544862310933d4", "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"],
            "uniswap": [self.list_providers["eth"], "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"]
        }
        return list_routers
    
    def get_user_args(self):
        self.user_args = input("Required information: " + Colors.YELLOW + "[ROUTER] [TOKEN ADDRESS] [BUY AMOUNT] [SLIPPAGE]\n" + Colors.STOP).split()
        if len(self.user_args) != 4:
            exit_error("Error: wrong number of arguments!")
        if not self.check_user_args():
            exit_error("Error: invalid arguments!")

    def check_user_args(self):
        if self.is_valid_router() and self.is_valid_address() and self.is_valid_nb(self.user_args[2]) and self.is_valid_nb(self.user_args[3]):
            self.user_args[2] = float(self.user_args[2])
            self.user_args[3] = float(self.user_args[3])
            return True
        return False

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
    
    def is_valid_nb(self, user_str):
        if re.search("^[0-9]+$", user_str) or re.search("^[0-9]+\.[0-9]+$", user_str):
            nb = float(user_str)
            if (nb > 0 and nb < 2 ** 256 - 1):
                return True
        return False

    def launch_bot(self):
        self.web3 = Web3(Web3.HTTPProvider(self.list_routers[self.user_args[0]][0]))
        if not self.web3.isConnected():
            exit_error("Error: bot was unable to connect to the provider!")
        self.router = self.web3.eth.contract(address=self.list_routers[self.user_args[0]][1], abi=convert_json("abi/uniswap_router_v2.json"))
        self.factory = self.web3.eth.contract(address=self.list_routers[self.user_args[0]][2], abi=convert_json("abi/uniswap_factory_v2.json"))
        self.wtoken = self.web3.eth.contract(address=self.router.functions.WETH().call(), abi=convert_json("abi/erc20.json"))
        print(Colors.GREEN + "Success: bot has been succesfully initialized." + Colors.STOP)
    
    def prepare_trade(self):
        buy_amount = int(self.user_args[2] * 10 ** self.wtoken.functions.decimals().call())
        path = [self.wtoken.address, self.user_args[1]]
        min_received_tokens = int(self.router.functions.getAmountsOut(buy_amount, path).call()[1] * 100 / (self.user_args[3] + 100))

        if self.wtoken.address == self.user_args[1]:
            exit_error("Error: you can't swap the same token!")
        if self.wtoken.functions.balanceOf(self.user_address).call() < buy_amount:
            exit_error("Error: you don't have enough wrapped tokens!")
        if self.wtoken.functions.allowance(self.user_address, self.router.address).call() < buy_amount:
            exit_error("Error: you didn't approve your wrapped tokens to be spent by the router!")

        if self.factory.functions.getPair(path[0], path[1]).call() == "0x0000000000000000000000000000000000000000":
            exit_error("Error: pair doesn't exist for this token!")

        buy_tx = self.router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(buy_amount, min_received_tokens, path, self.user_address, int(time.time() + 300)).buildTransaction(self.get_user_tx())
        #signed_buy_tx = self.web3.eth.account.sign_transaction(buy_tx, private_key=self.private_key)
        #tx_hash = self.web3.eth.send_raw_transaction(signed_buy_tx.rawTransaction)
        #sys.exit(Colors.GREEN + "Your transaction has been sent! Check its status on the explorer: " + str(tx_hash) + Colors.STOP)
    
    def get_user_tx(self):
        # add condition + variable to change value of gas according to blockchain
        user_tx = {
            "from": self.user_address,
            #"gas": 1000000,
            #"gasPrice": 5000000000,
            "nonce": self.web3.eth.getTransactionCount(self.user_address)
        }
        return user_tx

# add to BotControl class
def convert_json(file):
    with open(file) as f:
        return (json.load(f))

def exit_error(err_msg):
    sys.exit(Colors.RED + err_msg + Colors.STOP)

def main():
    env_values = dotenv_values(".env")
    bot = Bot(env_values["USER_ADDRESS"], env_values["PRIVATE_KEY"])

if __name__ == "__main__":
    main()