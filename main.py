import logging
from service import peer
from flask_ngrok import start_ngrok
import subprocess
from pathlib import Path
import yaml
import tempfile
import platform
import os
import time
import atexit

TEST = 1

def setAuthtoken(TOKEN):
    ngrok_path = str(Path(tempfile.gettempdir(), "ngrok"))
    system = platform.system()
    if system == "Darwin":
        command = "ngrok"
    elif system == "Windows":
        command = "ngrok.exe"
    elif system == "Linux":
        command = "ngrok"
    else:
        raise Exception(f"{system} is not supported")
    executable = str(Path(ngrok_path, command))
    os.chmod(executable, 777)
    print(ngrok_path)
    ngrok = subprocess.Popen([executable, 'authtoken', TOKEN])
    atexit.register(ngrok.terminate)
    time.sleep(1)

def readConfigFile():
    resourcePath = Path(Path.cwd(), "resources")
    logging.info("Resource path: "+ str(resourcePath))
    with open(Path.joinpath(resourcePath,"config.yml"), 'r') as f:
        yml_file = yaml.safe_load(f.read())
        return yml_file

def readAuthtoken():
    config_file = readConfigFile()
    authtoken = config_file['authtoken']
    return authtoken[peer.SELF_KEY]


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--node', default=1, type=int, help='this node number')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    # NODE_NUMBER = args.node
    host_ip =  peer.get_host_ip()
    
    peer.SELF_KEY = "localhost:" + repr(port)

    logging.info(f"SELF_KEY - {peer.SELF_KEY}")

    if(TEST):
        peer.peer_update(["localhost:5000", "localhost:5001", "localhost:5002", "localhost:5003"])
    else:
        peer.peer_insert(peer.get_my_key())

    # setAuthtoken(readAuthtoken())
    public_url = start_ngrok()
    readConfigFile()
    peer.app.run(port=port, debug=True, threaded=False)