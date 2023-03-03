import atexit
import json
import os
import platform
import shutil
import psutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from threading import Timer
from service.Storage import Storage
import requests

is_ngrok_running_ = False

def _is_ngrok_running():
    return is_ngrok_running_

def get_ngrok_stat():
    localhost_url = f"http://localhost:4040/api/tunnels/{SELF_KEY}"  # Url with tunnel details
    time.sleep(1)
    tunnel_url = requests.get(localhost_url).text  # Get the tunnel information
    j = json.loads(tunnel_url)

    tunnel_url = j['public_url']  # Do the parsing of the get
    tunnel_url = tunnel_url.replace("https", "http")
    pass

def _run_ngrok():
    global is_ngrok_running_
    global ngrok
    from .peer import SELF_KEY

    ngrok_path = str(Path(tempfile.gettempdir(), "ngrok"))
    _download_ngrok(ngrok_path)
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
    logfile = Storage().create_ngrok_log_file()
    ngrok = subprocess.Popen([executable, 'start', '--all', '--config', 'resources/config.yml'], stdout=logfile, stderr=logfile)
    
    if ngrok.poll() is None:
        is_ngrok_running_ = True

    atexit.register(ngrok.terminate)
    localhost_url = f"http://localhost:4040/api/tunnels/{SELF_KEY}"  # Url with tunnel details
    time.sleep(1)
    tunnel_url = requests.get(localhost_url).text  # Get the tunnel information
    j = json.loads(tunnel_url)

    tunnel_url = j['public_url']  # Do the parsing of the get
    tunnel_url = tunnel_url.replace("https", "http")
    return tunnel_url


def _download_ngrok(ngrok_path):
    if Path(ngrok_path).exists():
        return
    system = platform.system()
    if system == "Darwin":
        url = "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-darwin-amd64.zip"
    elif system == "Windows":
        url = "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-windows-amd64.zip"
    elif system == "Linux":
        url = "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip"
    else:
        raise Exception(f"{system} is not supported")
    download_path = _download_file(url)
    with zipfile.ZipFile(download_path, "r") as zip_ref:
        zip_ref.extractall(ngrok_path)


def _download_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    download_path = str(Path(tempfile.gettempdir(), local_filename))
    with open(download_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return download_path


def start_ngrok():
    ngrok_address = _run_ngrok()
    print(f" * Running on {ngrok_address}")
    print(f" * Traffic stats available on http://127.0.0.1:4040")


def run_with_ngrok(app):
    """
    The provided Flask app will be securely exposed to the public internet via ngrok when run,
    and the its ngrok address will be printed to stdout
    :param app: a Flask application object
    :return: None
    """
    old_run = app.run

    def new_run():
        thread = Timer(1, start_ngrok)
        thread.setDaemon(True)
        thread.start()
        old_run()
    app.run = new_run
