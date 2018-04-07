import os
from urllib.request import Request, urlopen
from web3 import Web3, HTTPProvider
from requests import ConnectionError

from rotkehlchen.utils import from_wei, rlk_jsonloads
from rotkehlchen.fval import FVal

import logging
logger = logging.getLogger(__name__)


class Ethchain(object):
    def __init__(self, ethrpc_port, attempt_connect=True):
        self.web3 = None
        self.rpc_port = ethrpc_port
        self.connected = False
        if attempt_connect:
            self.attempt_connect(ethrpc_port)

    def attempt_connect(self, ethrpc_port, mainnet_check=True):
        if self.rpc_port == ethrpc_port and self.connected:
            # We are already connected
            return True, 'Already connected to an ethereum node'

        if self.web3:
            del self.web3

        try:
            self.web3 = Web3(HTTPProvider('http://localhost:{}'.format(ethrpc_port)))
        except ConnectionError:
            logger.warn('Could not connect to a local ethereum node. Will use etherscan only')
            self.connected = False
            return False, 'Failed to connect to ethereum node at port {}'.format(ethrpc_port)

        if self.web3.isConnected():
            dir_path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(dir_path, 'data', 'token_abi.json'), 'r') as f:
                self.token_abi = rlk_jsonloads(f.read())

            # Also make sure we are actually connected to the Ethereum mainnet
            if mainnet_check:
                genesis_hash = self.web3.eth.getBlock(0)['hash']
                target = '0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3'
                if genesis_hash != target:
                    logger.warn(
                        'Connected to a local ethereum node but it is not on the ethereum mainnet'
                    )
                    self.connected = False
                    message = (
                        'Connected to ethereum node at port {} but it is not on '
                        'the ethereum mainnet'.format(ethrpc_port)
                    )
                    return False, message

            self.connected = True
            return True, ''
        else:
            logger.warn('Could not connect to a local ethereum node. Will use etherscan only')
            self.connected = False
            message = 'Failed to connect to ethereum node at port {}'.format(ethrpc_port)

        # If we get here we did not connnect
        return False, message

    def set_rpc_port(self, port):
        """ Attempts to set the RPC port for the ethereum client.

        Returns a tuple (result, message)
            - result: Boolean for success or failure of changing the rpc port
            - message: A message containing information on what happened. Can
                       be populated both in case of success or failure"""
        result, message = self.attempt_connect(port)
        if result:
            self.ethrpc_port = port
        return result, message

    def get_eth_balance(self, account):
        if not self.connected:
            eth_resp = urlopen(Request(
                'https://api.etherscan.io/api?module=account&action=balance&address=%s'
                % account
            ))
            eth_resp = rlk_jsonloads(eth_resp.read())
            if eth_resp['status'] != 1:
                raise ValueError('Failed to query etherscan for accounts balance')
            amount = FVal(eth_resp['result'])
            return from_wei(amount)
        else:
            return from_wei(self.web3.eth.getBalance(account))

    def get_multieth_balance(self, accounts):
        """Returns a dict with keys being accounts and balances in ETH"""
        balances = {}
        if not self.connected:
            # TODO: accounts.length should be less than 20. If more we gotta do
            # multiple calls
            eth_resp = urlopen(Request(
                'https://api.etherscan.io/api?module=account&action=balancemulti&address=%s' %
                ','.join(accounts)
            ))
            eth_resp = rlk_jsonloads(eth_resp.read())
            if eth_resp['status'] != 1:
                raise ValueError('Failed to query etherscan for accounts balance')
            eth_accounts = eth_resp['result']
            for account_entry in eth_accounts:
                amount = FVal(account_entry['balance'])
                balances[account_entry['account']] = from_wei(amount)

        else:
            for account in accounts:
                amount = FVal(self.web3.eth.getBalance(account))
                balances[account] = from_wei(amount)

        return balances

    def get_multitoken_balance(self, token_symbol, token_address, token_decimals, accounts):
        """Return a dictionary with keys being accounts and value balances of token
        Balance value is normalized through the token decimals.
        """
        balances = {}
        if self.connected:
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=self.token_abi
            )
            for account in accounts:
                token_amount = FVal(token_contract.call().balanceOf(account))
                if token_amount != 0:
                    balances[account] = token_amount / (FVal(10) ** FVal(token_decimals))
        else:
            for account in accounts:
                print('Checking token {} for account {}'.format(token_symbol, account))
                resp = urlopen(Request(
                    'https://api.etherscan.io/api?module=account&action='
                    'tokenbalance&contractaddress={}&address={}'.format(
                        token_address,
                        account,
                    )))
                resp = rlk_jsonloads(resp.read())
                if resp['status'] != 1:
                    raise ValueError(
                        'Failed to query etherscan for {} token balance of {}'.format(
                            token_symbol,
                            account,
                        ))
                token_amount = FVal(resp['result'])
                if token_amount != 0:
                    balances[account] = token_amount / (FVal(10) ** FVal(token_decimals))

        return balances

    def get_token_balance(self, token_symbol, token_address, token_decimals, account):
        res = self.get_multitoken_balance(token_symbol, token_address, token_decimals, [account])
        return res.get(account, 0)

    def get_block_by_number(self, num):
        if not self.connected:
            return None

        return self.web3.eth.getBlock(num)
