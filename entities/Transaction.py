from hashlib import sha256
from pathlib import Path
import base64

class Transaction:
    def __init__(self):
        self.id = ""
        self.type = ""
        self.initiator = ""
        self.payload = ""

    def add_payload(self, filename, initiator):
        with open("resources/"+filename, "rb") as file:
            bytes_read = file.read()
            data_encoded = base64.b64encode(bytes_read)
            self.payload = data_encoded.decode("ascii")

        self.id = sha256(base64.b64decode(self.payload)).hexdigest()
        self.type = "PUBLISH"
        self.initiator = initiator

    def add_tx_data(self, id, type, initiator, payload):
        self.id = id
        self.type = type
        self.initiator=initiator
        self.payload = payload
        return
    
    def payload_to_file(self, peerPath):
        dirName = peerPath.split(":")
        filePath = "resources/"+dirName[0]+"/"+dirName[1]
        Path(filePath).mkdir(parents=True, exist_ok=True)
        print(filePath)
        bytes_read = base64.b64decode(self.payload)
        with open(filePath+"/plugin.txt", 'wb') as f:
            f.write(bytes_read)

    def toJSON(self):
        return dict(id=self.id, type=self.type, initiator=self.initiator, payload=self.payload)