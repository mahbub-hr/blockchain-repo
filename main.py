import logging

from service import peer
TEST = 1

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
        peer.peer_update(["localhost:5000", "localhost:5001"])
    else:
        peer.peer_insert(peer.get_my_key())

    peer.app.run(port=port, debug=True, threaded=False)