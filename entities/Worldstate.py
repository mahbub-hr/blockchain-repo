class Worldstate:
    def __init__(self):
        self.worldstate = {}
        self.publickeys = {}
        '''with open("initial_balance.txt",'r') as f:
            for line in f:
                key, value = line.partition(" ")[::2]
                self.worldstate[key.strip()] = float(value)'''

    def insert(self, key, value, public_key):
        self.worldstate[key] = float(value)
        self.publickeys[key] = public_key
    
    def insert_no_crypt(self, key, value):
        self.worldstate[key] = float(value)

    def update(self, sender, receiver, amount):
        # need a check for double spending
        if self.worldstate[sender] < amount:
            return False

        self.worldstate[sender] = self.worldstate[sender] - amount
        self.worldstate[receiver] = self.worldstate[receiver] + amount
        #return a list of valid and invalid transactions
        return True
    def update_with_block(self,block):
        update_log = {}
        update_log['valid'] = []
        update_log['invalid'] = []
        
        for tx in block.transactions:
            ret=self.update(tx['sender'], tx['recipient'], tx['amount'])
            if not ret:
                update_log['invalid'].append(tx)
            update_log['valid'].append(tx)
        return update_log

    def get(self, key):
        return self.worldstate[key]

    def print(self):
        print(json.dumps(self.worldstate, indent=4))