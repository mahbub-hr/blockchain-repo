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
from entities.Blockchain import Blockchain
app = Flask(__name__)


from base64 import (
    b64encode,
    b64decode,
)

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(message)s', datefmt='%H:%M:%S')



SELF_KEY = ""
PREV_HASH=""
bchain = Blockchain.Blockchain()
PREV_HASH = bchain.chain[0].hash
worldstate = blockchain.Worldstate()

peers = []

@app.route('/init_node', methods=['GET'])
def initi_peer():

    peer_insert(SELF_KEY)
    
    return "Peer Reset - Done", 200

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

@app.route('/ps_util', methods=['GET'])
def memory_usage_psutil():
    # return the memory usage in MB
    
    process = psutil.Process(os.getpid())
    mem = (process.memory_info()[0])/float(2**20) 
    return mem

def get_obj_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))

        # Lookup all the object referred to by the object in obj_q.
        # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        # Using dict notation will prevent repeated objects.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will
        # not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return sz

@app.route('/getsize', methods=['GET'])
def getchainsize():
    #global bchain
    #block_size = get_obj_size(bchain.chain[1])
    if SELF_KEY in tracker.node_to_shard:
        num_of_shard = len(tracker.node_to_shard[SELF_KEY])
        
    else:
        num_of_shard =0
       

    element = len(bchain.chain)
    
    return json.dumps(f'{SELF_KEY},{OVERLAPPING},{num_of_shard},{element},{get_obj_size(bchain)}, {memory_usage_psutil()}\n'), 200

#act as a orderer
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    return

def verify_and_add_block(block_index):
    return

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    for block in bchain.chain:
        chain_data.append(block.__dict__)

    response = json.dumps(
        {"length": len(chain_data),
         "chain": chain_data,
         "peers": peers,
         "worldstate": worldstate.worldstate})

    return response

@app.route('/printpeer')
def showpeer():
    global peers
    logging.info(f"peers - {peers}")
    return 'Printed', 200

@app.route('/peer_update_on_registration', methods=['POST'])
def reg_update():
    updated_peerlist = request.get_json()["updated_peerlist"]
    peer_update(updated_peerlist)
    return "New Peer emerged, list updated", 200

# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    data = {
        'updated_peerlist': peers
    }
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peer_insert(node_address)
    peer_broadcast('peer_update_on_registration', data, {SELF_KEY, node_address})
    if IS_SHARDED:
        return sharded_chain(node_address)
    else:
        return full_chain()

@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]

    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    response = requests.post(node_address + "/register_node",
                             json=data, headers=headers)

    if response.status_code == 200:
        global bchain
        #this is in master
        global peers
        global worldstate
        global LAST_INDEX
        # update chain and the peers
        json_data = response.json()
        chain_dump = json_data['chain']
        
        if IS_SHARDED:
            t = json_data['tracker']
            tracker.node_to_shard = t['node_to_shard']
            tracker.shard_to_node = t['shard_to_node']
        # need to remove if there is a seperate orderer
        LAST_INDEX = bchain.chain[-1].index + 1
        peer_update(json_data['peers'])
        #print(peers)
        worldstate.worldstate = json_data['worldstate']
        return jsonify("Registration successful"), 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


@app.route('/sendnewnodeinfo', methods=['POST'])
def get_new_node_info():
    global tracker
    response = request.get_json()
    track = response['track']
    tracker_ = response['tracker']
    node_address = response['node_address']
    tracker.node_to_shard=tracker_['node_to_shard']
    tracker.shard_to_node=tracker_['shard_to_node']
    peer_insert(node_address)

    node_to_shard = track['node_to_shard']
    if SELF_KEY not in node_to_shard:
        return "get new node info returned wihtout sending any shard"
    shards = bchain.remove_multiple_shards(node_to_shard[SELF_KEY], SHARD_SIZE)
    #logging.info(f"{send_shard_to(shards, node_address)}")
    return 'get new node info returned', 200

def create_chain_from_dump(chain_dump):
    generated_blockchain = blockchain.Blockchain()
    # generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0 and not IS_SHARDED:
            continue  # skip genesis block
        block = blockchain.Block(block_data["index"],
                                 block_data["transactions"],
                                 block_data["timestamp"],
                                 block_data["previous_hash"])
        block.hash = block_data['hash']
        if IS_SHARDED:
            #integraty check is not performed

            added= generated_blockchain.add_block_on_shard(block,'')
        else:
            added = generated_blockchain.add_block(block)

        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain

@app.route('/txbysender', methods=['POST'])
def txbysender():
    data = request.get_json()
    sender = data['sender']
    shard = data['shard']

    tx_list = tx_in_shard_by_sender(sender, shard)
    return json.dumps({'tx': tx_list})


@app.route("/wholeshardquery", methods=['POST'])
def wholeshardquery():
    data = request.get_json()
    sender = data['sender']
    tx = []
    time_stats = {}
    start = time.time()

    for shard in tracker.shard_to_node:
        peer = tracker.shard_to_node[shard][0]

        if (peer != SELF_KEY) and tracker.node_to_shard[peer]:
            data['shard'] = shard
            s = time.time()
            response = requests.post(peer + "txbysender", json=data, headers={"Content-Type": 'application/json'})
            e = time.time()
            tx.extend(response.json()['tx'])
        else:
            s = time.time()
            tx.extend(tx_in_shard_by_sender(sender, shard))
            e = time.time()
        
        stats ={}
        stats['peer'] = peer
        stats['time'] = e - s
        time_stats[shard] = stats

    end = time.time()
    total_elapsed = end-start

    time_stats['total'] = total_elapsed
    response= {
                "tx":tx,
                "time_stats":time_stats
                }

    return json.dumps(response),200


@app.route("/query", methods=['POST'])
def query():
    data = request.get_json()
    return repr(worldstate.get(data['key'])), 200


@app.route("/printworldstate", methods=['GET'])
def printWorldstate():
    worldstate.print()
    return "print worldstate"

@app.route('/printtracker',methods=['GET'])
def print_tracker():
    tracker.print()
    return 'print tracker'

@app.route("/printchainwithtxs", methods=['GET'])
def printchainwithtxs():
    logging.info(f"Total Blocks - {len(bchain.chain)} Current chain - ")
    for block in bchain.chain:
        print(json.dumps(block.__dict__, indent=4))

    return "print chain"

@app.route("/printchain", methods=['GET'])
def printchain():
    logging.info(f"Total Blocks - {len(bchain.chain)} Current chain - ")
    for block in bchain.chain:
        temp_block = copy.deepcopy(block.__dict__)
        del temp_block["transactions"]
        print(json.dumps(temp_block, indent=4))
    return "print chain without txs"


def peer_broadcast_thread(url, data, header={"Content-Type": 'application/json'}):
    response = requests.post(url, json = data, headers=header)
    #logging.info(f"response of broadcast from {url} - {response.content}")

def peer_broadcast(url, data, exclude, header={"Content-Type": 'application/json'}):
    for peer in peers:
        if peer not in exclude:
            t = threading.Thread(target=peer_broadcast_thread, args=(peer+url, data, header, ))
            t.start()
    return "peer broadcast returned"

@app.route("/", methods=['GET'])
def home():
    print("tested ")
    return "<html>\
                <body><h1> Welcome to Homepage</h1></body>\
            </html>"

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        logging.info(f"can not get host name and ip address")

def get_ext_ip():
    ip = requests.get('https://api.ipify.org').text 
    logging.info(f'My public IP address is: {ip}')
    return ip

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


