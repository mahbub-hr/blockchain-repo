from hashlib import sha256
import json
from entities import Transaction
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash  # Adding the previous hash field

    def compute_hash(self):
        block_string = json.dumps(self.toJSON(), cls=ComplexEncoder,sort_keys=True)  # The string equivalent also considers the previous_hash field now
        self.hash = sha256(block_string.encode()).hexdigest()
        return self.hash

    def persist_bock(self):
        filename = repr(self.index) + ".block"
        with open(filename, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
        return

    def load_block(self):
        pass

    def block_DTO(self):
        output = {}
        transactions = {}

        output["index"] = self.index
        output["timestamp"] = self.timestamp
        output["previous_hash"] = self.previous_hash
        output["tx_id"] = self.transactions[0].id
        output["tx_type"] = self.transactions[0].type
        output["tx_initiator"] = self.transactions[0].initiator
        output['tx_payload'] = self.transactions[0].payload

        return output

    def toJSON(self):
        return dict(index=self.index, transactions=self.transactions, timestamp=self.timestamp, previous_hash=self.previous_hash)

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'toJSON'):
            return obj.toJSON()
        else:
            return json.JSONEncoder.default(self, obj)