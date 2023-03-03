import requests
import json
import time
import sys
import socket 
import math
import gc
import psutil
import os
from flask import Flask, jsonify, request
import threading
import logging
import copy
from entities import (
    Blockchain,
    Block,
    Transaction
)

from base64 import (
    b64encode,
    b64decode,
)

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)



SELF_KEY = ""
PREV_HASH=""
bchain = Blockchain.Blockchain()
PREV_HASH = bchain.chain[0].hash

peers = []

def peer_insert(p):
    if p not in peers:
        peers.append(p)
    else:
        logging.info(f"{p} already exists")


def peer_update(peer):
    for p in peer:
        if p not in peers:
            peers.append(p)

def get_my_key():
    if SELF_KEY == "":
        logging.info(f"key is not set")
        return ""
    return SELF_KEY
 
def get_block_from_DTO(block_DTO):
        tx = Transaction.Transaction() 
        tx.add_tx_data(block_DTO['tx_id'], block_DTO['tx_type'], block_DTO['tx_initiator'], block_DTO['tx_payload'])
        transactions = []
        transactions.append(tx)
        block = Block.Block(block_DTO['index'], transactions, block_DTO['timestamp'], block_DTO['previous_hash'])
        block.compute_hash()
        return block

@app.route('/receive_block', methods=['POST'])
def recieve_block():
    new_block_DTO = request.get_json()
    new_block = get_block_from_DTO(new_block_DTO)
    bchain.add_block(new_block, "")
    return {"status":200, "message": "Success"}

@app.route('/mine', methods=['POST'])
def new_transaction():
    mined_block = bchain.mine()
    peer_broadcast("/receive_block", data=mined_block.block_DTO(), exclude={})
    return {"status":200, "message": "Success"}

@app.route('/publish_plugin', methods=['POST'])
def publish_plugin():
    filename = request.get_json()["file"]
    bchain.new_transaction(filename=filename, SELF_KEY=SELF_KEY)
    return {"status":200, "message": "Success"}

def verify_and_add_block(block_index):
    return

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    
    response = json.dumps(
        bchain.toJSON(), cls=Block.ComplexEncoder)

    return response

@app.route('/downloadPlugin', methods=['POST'])
def download_plugin():
    response = request.get_json()
    plugin_id = response["id"]
    try:
        bchain.download_plugin(plugin_id, SELF_KEY)
    except:
        return {"status":210, "message":"Could not download the plugin"}

    return {"status":200, "message":"Plugin downloaded successfully"}

@app.route('/peer_update_on_registration', methods=['POST'])
def reg_update():
    updated_peerlist = request.get_json()["updated_peerlist"]
    peer_update(updated_peerlist)
    return "New Peer emerged, list updated", 200

# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    print(request)
    node_address = request.get_json()["node_address"]
    data = {
        'updated_peerlist': peers
    }
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peer_insert(node_address)
    peer_broadcast('peer_update_on_registration', data, {SELF_KEY, node_address})
    
    return full_chain()

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]

    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    print(node_address)
    headers = {'Content-Type': "application/json"}

    response = requests.post(node_address + "/register_node",
                             json=data, headers=headers)

    if response.status_code == 200:
        return jsonify("Registration successful"), 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code

def peer_broadcast_thread(url, data, header={"Content-Type": 'application/json'}):
    response = requests.post(url, json = data, headers=header)
    logging.info(f"response of broadcast from {url} - {response.content}")

def peer_broadcast(url, data, exclude, header={"Content-Type": 'application/json'}):
    for peer in peers:
        if peer not in exclude and peer != SELF_KEY:
            logging.info(f"Sending update to : {peer}")
            t = threading.Thread(target=peer_broadcast_thread, args=("http://"+peer+url, data, header, ))
            t.start()
    return "peer broadcast returned"

@app.route("/", methods=['GET'])
def home():
    print("tested ")
    return f"<html>\
                <body><h1> Welcome to Homepage</h1><p>{SELF_KEY}</p></body>\
            </html>"
            
@app.route('/printpeer')
def showpeer():
    global peers
    logging.info(f"peers - {peers}")
    return 'Printed', 200

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        logging.info(f"can not get host name and ip address")

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


