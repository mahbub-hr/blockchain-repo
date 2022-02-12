from service import peer

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--node', default=1, type=int, help='this node number')
    args = parser.parse_args()
    port = args.port
    NODE_NUMBER = port
    # NODE_NUMBER = args.node
    host_ip =  get_host_ip()
    
    SELF_KEY = "http://" + get_ext_ip() + ":" + repr(port)+"/"
    logging.info(f"SELF_KEY - {SELF_KEY}")
    peer_insert(get_my_key())
    app.run(host=host_ip, port=port, debug=True, threaded=False)