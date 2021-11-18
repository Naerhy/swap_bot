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

# check return values of some functions => check errors
# find a way to determine gas price depending of blockchain (check x past blocks for transactions, get the median and * 2)
# build GUI + exec => use whitelist system with custom .sol contract as a requirement to use bot
# rename title bot
# add get price token feature
# add color to titles and separators
# get correct tx hash => use __dict__ or __class__ ?
# add stop button for swap (stop looking for pair being created)

class Control:
    @staticmethod
    def convert_json(file):
        with open(file) as f:
            return (json.load(f))

    @staticmethod
    def parse_swap(user_input):
        if user_input["router"] \
        and Web3.isAddress(user_input["input_token"]) \
        and Web3.isAddress(user_input["output_token"]) \
        and user_input["input_token"] != user_input["output_token"] \
        and Control.is_valid_nb(user_input["buy_amount"]) \
        and Control.is_valid_nb(user_input["slippage"]):
            return True
        return False
    
    @staticmethod
    def parse_approve(user_input):
        if user_input["router"] and Web3.isAddress(user_input["token"]):
            return True
        return False

    @staticmethod
    def is_valid_nb(user_str):
        if re.search("^[0-9]+$", user_str) or re.search("^[0-9]+\.[0-9]+$", user_str):
            nb = float(user_str)
            if (nb > 0 and nb <= 2 ** 256 - 1):
                return True
        return False

    @staticmethod
    def convert_user_input(user_input):
        for x in user_input:
            if x == "input_token" or x == "output_token" or x == "token":
                user_input[x] = Web3.toChecksumAddress(user_input[x])
            if x == "buy_amount" or x == "slippage":
                user_input[x] = float(user_input[x])
        return user_input

class Bot:
    def __init__(self, user_address, private_key):
        self.user_address = user_address
        self.private_key = private_key
        self.list_routers = self.get_list_routers()
    
    def get_list_routers(self):
        providers = self.get_list_providers()
        routers = {
        "Pangolin": [providers["avax"], "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106", "0xefa94DE7a4656D787667C749f7E1223D71E9FD88"],
        "Traderjoe": [providers["avax"], "0x60aE616a2155Ee3d9A68541Ba4544862310933d4", "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"],
        "Apeswap": [providers["bsc"], "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7", "0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6"],
        "Pancakeswap": [providers["bsc"], "0x10ED43C718714eb63d5aA57B78B54704E256024E", "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"],
        "Sushiswap": [providers["eth"], "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"],
        "Uniswap": [providers["eth"], "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"],
        "Spiritswap": [providers["ftm"], "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52", "0xEF45d134b73241eDa7703fa787148D9C9F4950b0"],
        "Spookyswap": [providers["ftm"], "0xF491e7B69E4244ad4002BC14e878a34207E38c29", "0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3"],
        "Quickswap": [providers["polygon"], "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"]
        }
        return routers

    def get_list_providers(self):
        providers = {
        "avax": "https://api.avax.network/ext/bc/C/rpc",
        "bsc": "https://bsc-dataseed1.defibit.io",
        "eth": "https://rpc.flashbots.net",
        "ftm": "https://rpc.ftm.tools",
        "polygon": "https://polygon-rpc.com"
        }
        return providers

    def prepare_swap(self, user_input):
        if Control.parse_swap(user_input):
            user_input = Control.convert_user_input(user_input)
            web3 = Web3(Web3.HTTPProvider(self.list_routers[user_input["router"]][0]))
            if web3.isConnected():
                router = web3.eth.contract(address=self.list_routers[user_input["router"]][1], abi=Control.convert_json("abi/uniswap_router_v2.json"))
                factory = web3.eth.contract(address=self.list_routers[user_input["router"]][2], abi=Control.convert_json("abi/uniswap_factory_v2.json"))
                try:
                    input_token = web3.eth.contract(address=user_input["input_token"], abi=Control.convert_json("abi/erc20.json"))
                    buy_amount = int(user_input["buy_amount"] * 10 ** input_token.functions.decimals().call())
                    if input_token.functions.balanceOf(self.user_address).call() >= buy_amount:
                        if input_token.functions.allowance(self.user_address, router.address).call() >= buy_amount:
                            self.app.thread(self.loop_swap, web3, router, factory, buy_amount, user_input)
                        else:
                            self.set_label_information("The router can't spend your wtokens, approve!", "label_swap_information", "red")
                    else:
                        self.set_label_information("You don't hold enough wtokens!", "label_swap_information", "red")
                except:
                    self.set_label_information("Input token isn't an ERC20 address!", "label_swap_information", "red")
            else:
                self.set_label_information("Bot was unable to connect to the provider!", "label_swap_information", "red")
        else:
            self.set_label_information("Invalid arguments!", "label_swap_information", "red")

    def loop_swap(self, web3, router, factory, buy_amount, user_input):
        path = [user_input["input_token"], user_input["output_token"]]
        i = 1
        while factory.functions.getPair(path[0], path[1]).call() == "0x0000000000000000000000000000000000000000":
            self.app.queueFunction(self.set_label_information, "No liquidity, looping(" + str(i) + ")...", "label_swap_information", "red")
            i += 1
            time.sleep(1)
        pair = web3.eth.contract(address=factory.functions.getPair(path[0], path[1]).call(), abi=Control.convert_json("abi/pair.json"))
        if path[0] == pair.functions.token0().call():
            pooled_tokens = pair.functions.getReserves().call()[0]
        else:
            pooled_tokens = pair.functions.getReserves().call()[1]
        if buy_amount <= pooled_tokens / 10:
            min_received_tokens = int(router.functions.getAmountsOut(buy_amount, path).call()[1] * 100 / (user_input["slippage"] + 100))
            try:
                buy_tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(buy_amount, min_received_tokens, path, self.user_address, int(time.time() + 300)).buildTransaction(self.get_user_tx(web3))
                signed_buy_tx = web3.eth.account.sign_transaction(buy_tx, private_key=self.private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_buy_tx.rawTransaction)
                self.app.queueFunction(self.set_label_information, "Your transaction has been sent!", "label_swap_information", "green")
                #self.set_label_information("Your transaction has been sent! Check its status on the explorer: " + str(tx_hash), "label_swap_information", "green")
            except:
                self.app.queueFunction(self.set_label_information, "An error occured during contract execution!", "label_swap_information", "red")
        else:
            self.app.queueFunction(self.set_label_information, "Slippage too high!", "label_swap_information", "red")
            
    def prepare_approve(self, user_input):
        if Control.parse_approve(user_input):
            user_input = Control.convert_user_input(user_input)
            web3 = Web3(Web3.HTTPProvider(self.list_routers[user_input["router"]][0]))
            if web3.isConnected():
                try:
                    token = web3.eth.contract(address=user_input["token"], abi=Control.convert_json("abi/erc20.json"))
                    self.approve(web3, token, self.list_routers[user_input["router"]][1])
                except:
                    self.set_label_information("Token isn't an ERC20 address!", "label_approve_information", "red")
            else:
                self.set_label_information("Bot was unable to connect to the provider!", "label_approve_information", "red")  
        else:
            self.set_label_information("Invalid arguments", "label_approve_information", "red")

    def approve(self, web3, token, router):
        try:
            approve_tx = token.functions.approve(router, 2 ** 256 - 1).buildTransaction({"from": self.user_address, "nonce": web3.eth.getTransactionCount(self.user_address)})
            signed_swap_tx = web3.eth.account.sign_transaction(approve_tx, private_key=self.private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_swap_tx.rawTransaction)
            self.set_label_information("Your transaction has been sent!", "label_approve_information", "green")
        except:
            self.set_label_information("An error occured during contract execution!", "label_approve_information", "red")

    # move this function to Control if possible:
    def get_user_tx(self, web3):
        # add condition + variable to change value of gas according to blockchain
        user_tx = {
            "from": self.user_address,
            #"gas": 1000000,
            #"gasPrice": 5000000000,
            "nonce": web3.eth.getTransactionCount(self.user_address)
        }
        return user_tx

class GUI(Bot):
    def __init__(self, user_address, private_key):
        super().__init__(user_address, private_key)
        self.app = gui("Bot")
        self.app.setResizable(False)
        self.app.setPadding(2, 2)
        self.create_swap_tab()
        self.create_approve_tab()

    def create_swap_tab(self):
        self.app.addLabel("label_swap_title", "Swap your tokens:", 0, 0, 2, 1)

        self.app.addLabel("label_swap_router", "Router", 1, 0, 1, 1)
        self.app.addLabel("label_swap_input_token", "Input token", 2, 0, 1, 1)
        self.app.addLabel("label_swap_output_token", "Output token", 3, 0, 1, 1)
        self.app.addLabel("label_swap_buy_amount", "Buy amount", 4, 0, 1, 1)
        self.app.addLabel("label_swap_slippage", "Slippage", 5, 0, 1, 1)

        self.app.addOptionBox("entry_swap_router", ["- Choose a router -", "- AVAX -", "Pangolin", "Traderjoe", "- BSC -", "Apeswap", "Pancakeswap", "- ETH -", "Sushiswap", "Uniswap", "- FTM -", "Spiritswap", "Spookyswap", "- Polygon -", "Quickswap"], 1, 1, 1, 1)
        self.app.addEntry("entry_swap_input_token", 2, 1, 1, 1)
        self.app.addEntry("entry_swap_output_token", 3, 1, 1, 1)
        self.app.addEntry("entry_swap_buy_amount", 4, 1, 1, 1)
        self.app.addEntry("entry_swap_slippage", 5, 1, 1, 1)

        self.app.addEmptyLabel("label_swap_information", 6, 0, 2, 1)

        self.app.addButtons(["Swap"], self.press_button, 7, 0, 2, 1)

        self.app.addLabel("label_separator_1", "==============================", 8, 0, 2, 1)
    
    def create_approve_tab(self):
        self.app.addLabel("label_approve_title", "Approve your tokens:", 9, 0, 2, 1)

        self.app.addLabel("label_approve_router", "Router", 10, 0, 1, 1)
        self.app.addLabel("label_approve_token", "Token", 11, 0, 1, 1)

        self.app.addOptionBox("entry_approve_router", ["- Choose a router -", "- AVAX -", "Pangolin", "Traderjoe", "- BSC -", "Apeswap", "Pancakeswap", "- ETH -", "Sushiswap", "Uniswap", "- FTM -", "Spiritswap", "Spookyswap", "- Polygon -", "Quickswap"], 10, 1, 1, 1)
        self.app.addEntry("entry_approve_token", 11, 1, 1, 1)

        self.app.addEmptyLabel("label_approve_information", 12, 0, 2, 1)

        self.app.addButtons(["Approve"], self.press_button, 13, 0, 2, 1)
    
    def press_button(self, button):
        if button == "Swap":
            user_input = {
                "router": self.app.getOptionBox("entry_swap_router"),
                "input_token": self.app.getEntry("entry_swap_input_token"),
                "output_token": self.app.getEntry("entry_swap_output_token"),
                "buy_amount": self.app.getEntry("entry_swap_buy_amount"),
                "slippage": self.app.getEntry("entry_swap_slippage")
            }
            self.prepare_swap(user_input)
        elif button == "Approve":
            user_input = {
                "router": self.app.getOptionBox("entry_approve_router"),
                "token": self.app.getEntry("entry_approve_token")
            }
            self.prepare_approve(user_input)

    def set_label_information(self, message, label_id, color):
        self.app.setLabelFg(label_id, color)
        self.app.setLabel(label_id, message) 

def main():
    env_values = dotenv_values(".env")
    program = GUI(env_values["USER_ADDRESS"], env_values["PRIVATE_KEY"])
    program.app.go()

if __name__ == "__main__":
    main()