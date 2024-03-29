from hashlib import sha256
import time
import json
import pickle
from urllib.parse import urlparse

from .Block import (
    Block,
    ComplexEncoder
)
from .Transaction import Transaction

class Blockchain:
    difficulty = 1
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False

        self.chain.append(block)
        self.current_transactions = []
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        # while not computed_hash.startswith('0' * Blockchain.difficulty):
        #     block.nonce += 1
        #     computed_hash = block.compute_hash()
        return computed_hash

    def new_transaction(self, filename, SELF_KEY):
        tx = Transaction()
        tx.add_payload(filename, SELF_KEY)
        self.current_transactions.append(tx)

        return self.last_block.index + 1

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.current_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.current_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.current_transactions = []
        return new_block

    def download_plugin(self, id, selfKey):
        for block in self.chain:
            print(json.dumps(block.toJSON(), cls=ComplexEncoder))
            
            tx = block.transactions
            if tx and tx[0].id == id:
                tx[0].payload_to_file(selfKey)

    def toJSON(self):
        return dict(chain=self.chain)

    def persist_chain(self):
        """
        save blockchain to disk
        :return:
        """
        size = len(self.chain)
        for i in range(size):
            self.chain[i].persist_block()
        return
