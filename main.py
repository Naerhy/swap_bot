# pip install web3
# pip install python-dotenv
# pip3 install appjar

from web3 import Web3
from dotenv import dotenv_values
from appJar import gui
import json
import re
import sys
import time

# reorganize the code with better classes + inheritance 
# define setters/getters ?
# check return values of some functions => check errors
# find a way to determine gas price depending of blockchain (check x past blocks for transactions, get the median and * 2)
# build GUI + exec => use whitelist system with custom .sol contract as a requirement to use bot
# add loop until liquidity is added feature
# find a way to detect if token address != ERC20 => avoid solidity errors => use try/catch exception?
# add a way to sell your bought tokens + buy with any token??
# rename title bot
# add get price token feature
# add color to titles and separators

class Bot:
    def __init__(self, user_address, private_key):
        self.user_address = user_address
        self.private_key = private_key
        self.list_providers = self.get_list_providers()
        self.list_routers = self.get_list_routers()
        self.create_app()

    def create_app(self):
        self.app = gui("Bot")
        self.app.setResizable(False)
        self.app.setPadding(2, 2)

        self.app.addLabel("label_swap_title", "Swap your tokens:", 0, 0, 2, 1)

        self.app.addLabel("label_swap_router", "Router", 1, 0, 1, 1)
        self.app.addLabel("label_swap_input_token", "Input token", 2, 0, 1, 1)
        self.app.addLabel("label_swap_output_token", "Output token", 3, 0, 1, 1)
        self.app.addLabel("label_swap_buy_amount", "Buy amount", 4, 0, 1, 1)
        self.app.addLabel("label_swap_slippage", "Slippage", 5, 0, 1, 1)

        self.app.addOptionBox("entry_swap_router", ["- Choose a router -", "- AVAX -", "Pangolin", "Traderjoe", "- BSC -", "Apeswap", "Pancakeswap", "- ETH -", "Sushiswap", "Uniswap", "- FTM -", "JetswapFTM", "Spiritswap", "Spookyswap", "- Polygon -", "Quickswap"], 1, 1, 1, 1)
        self.app.addEntry("entry_swap_input_token", 2, 1, 1, 1)
        self.app.addEntry("entry_swap_output_token", 3, 1, 1, 1)
        self.app.addEntry("entry_swap_buy_amount", 4, 1, 1, 1)
        self.app.addEntry("entry_swap_slippage", 5, 1, 1, 1)

        self.app.addEmptyLabel("label_swap_information", 6, 0, 2, 1)

        self.app.addButtons(["Swap"], self.send_user_input, 7, 0, 2, 1)

        self.app.addLabel("label_separator_1", "==============================", 8, 0, 2, 1)

        self.app.addLabel("label_approve_title", "Approve your tokens:", 9, 0, 2, 1)

        self.app.addLabel("label_approve_router", "Router", 10, 0, 1, 1)
        self.app.addLabel("label_approve_token", "Token", 11, 0, 1, 1)

        self.app.addOptionBox("entry_approve_router", ["- Choose a router -", "- AVAX -", "Pangolin", "Traderjoe", "- BSC -", "Apeswap", "Pancakeswap", "- ETH -", "Sushiswap", "Uniswap", "- FTM -", "JetswapFTM", "Spiritswap", "Spookyswap", "- Polygon -", "Quickswap"], 10, 1, 1, 1)
        self.app.addEntry("entry_approve_token", 11, 1, 1, 1)

        self.app.addEmptyLabel("label_approve_information", 12, 0, 2, 1)

        self.app.addButtons(["Approve"], self.send_user_input, 13, 0, 2, 1)

        self.app.go()

    def send_user_input(self):
        user_input_swap = {
            "router": self.app.getOptionBox("entry_swap_router"),
            "input_token": self.app.getEntry("entry_swap_input_token"),
            "output_token": self.app.getEntry("entry_swap_output_token"),
            "buy_amount": self.app.getEntry("entry_swap_buy_amount"),
            "slippage": self.app.getEntry("entry_swap_slippage")
        }
        self.init_bot(user_input_swap)

    def set_label_information(self, message, label_id, color):
            self.app.setLabelFg(label_id, color)
            self.app.setLabel(label_id, message) 

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
        # provider - router - factory
        list_routers = {
            "Pangolin": [self.list_providers["avax"], "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106", "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"],
            "Traderjoe": [self.list_providers["avax"], "0x60aE616a2155Ee3d9A68541Ba4544862310933d4", "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"],
            "Apeswap": [self.list_providers["bsc"], "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7", "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6"],
            "Pancakeswap": [self.list_providers["bsc"], "0x10ED43C718714eb63d5aA57B78B54704E256024E", "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"],
            "Sushiswap": [self.list_providers["eth"], "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"],
            "Uniswap": [self.list_providers["eth"], "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"],
            "JetswapFTM": [self.list_providers["ftm"], "0x845E76A8691423fbc4ECb8Dd77556Cb61c09eE25", "0xf6488205957f0b4497053d6422F49e27944eE3Dd"],
            "Spiritswap": [self.list_providers["ftm"], "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52", "0xEF45d134b73241eDa7703fa787148D9C9F4950b0"],
            "Spookyswap": [self.list_providers["ftm"], "0xF491e7B69E4244ad4002BC14e878a34207E38c29", "0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3"],
            "Quickswap": [self.list_providers["polygon"], "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"]
        }
        return list_routers

    def check_user_input(self, user_input):
        if user_input["router"] and Web3.isAddress(user_input["input_token"]) and Web3.isAddress(user_input["output_token"]) and self.is_valid_nb(user_input["buy_amount"]) and self.is_valid_nb(user_input["slippage"]):
            return True
        return False
    
    def is_valid_nb(self, user_str):
        if re.search("^[0-9]+$", user_str) or re.search("^[0-9]+\.[0-9]+$", user_str):
            nb = float(user_str)
            if (nb > 0 and nb < 2 ** 256 - 1):
                return True
        return False
    
    def convert_user_input(self, user_input):
        user_input["input_token"] = Web3.toChecksumAddress(user_input["input_token"])
        user_input["output_token"] = Web3.toChecksumAddress(user_input["output_token"])
        user_input["buy_amount"] = float(user_input["buy_amount"])
        user_input["slippage"] = float(user_input["slippage"])
        return user_input

    def init_bot(self, user_input):
        if self.check_user_input(user_input):
            user_input = self.convert_user_input(user_input)
            self.web3 = Web3(Web3.HTTPProvider(self.list_routers[user_input["router"]][0]))
            if self.web3.isConnected():
                self.router = self.web3.eth.contract(address=self.list_routers[user_input["router"]][1], abi=convert_json("abi/uniswap_router_v2.json"))
                self.factory = self.web3.eth.contract(address=self.list_routers[user_input["router"]][2], abi=convert_json("abi/uniswap_factory_v2.json"))
                self.input_token = self.web3.eth.contract(address=user_input["input_token"], abi=convert_json("abi/erc20.json"))
                self.swap(user_input)
            else:
                self.set_label_information("Bot was unable to connect to the provider!", "label_swap_information", "red")
        else:
            self.set_label_information("Invalid arguments!", "label_swap_information", "red")
    
    def swap(self, user_input):
        buy_amount = int(user_input["buy_amount"] * 10 ** self.input_token.functions.decimals().call())
        path = [user_input["input_token"], user_input["output_token"]]

        if path[0] != path[1]: # add this line to parsing function
            if self.input_token.functions.balanceOf(self.user_address).call() >= buy_amount:
                if self.input_token.functions.allowance(self.user_address, self.router.address).call() >= buy_amount:
                    if self.factory.functions.getPair(path[0], path[1]).call() != "0x0000000000000000000000000000000000000000":
                        min_received_tokens = int(self.router.functions.getAmountsOut(buy_amount, path).call()[1] * 100 / (user_input["slippage"] + 100))
                        try:
                            buy_tx = self.router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(buy_amount, min_received_tokens, path, self.user_address, int(time.time() + 300)).buildTransaction(self.get_user_tx())
                            signed_buy_tx = self.web3.eth.account.sign_transaction(buy_tx, private_key=self.private_key)
                            tx_hash = self.web3.eth.send_raw_transaction(signed_buy_tx.rawTransaction)
                            self.set_label_information("Your transaction has been sent! Check its status on the explorer: " + str(tx_hash), "label_swap_information", "green")
                        except:
                            self.set_label_information("An error occured during contract execution!", "label_swap_information", "red")
                    else:
                        self.set_label_information("The pair doesn't exist for this token!", "label_swap_information", "red")
                else:
                    self.set_label_information("The router can't spend your wtokens, approve!", "label_swap_information", "red")
            else:
                self.set_label_information("You don't hold enough wtokens!", "label_swap_information", "red")
        else:
            self.set_label_information("You can't swap the same token!", "label_swap_information", "red")
    
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

def main():
    env_values = dotenv_values(".env")
    bot = Bot(env_values["USER_ADDRESS"], env_values["PRIVATE_KEY"])

if __name__ == "__main__":
    main()