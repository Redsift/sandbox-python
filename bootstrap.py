import imp
import json
import os
import os.path
import sys
import threading
import time

from nanomsg import Socket, REP

def env_var_or_exit(n):
    v = os.environ.get(n)
    if not v:
        print n + ' not set'
        sys.exit(1)
    return v

def new_module(node_idx, src):
    n = 'node%d' % node_idx
    m = imp.new_module(n)
    exec open(src).read() in m.__dict__
    if not hasattr(m, 'compute'):
        print '"%s" does not implement compute function' % src
        sys.exit(1)
    # We could register our module under `sys.modules[n]`, but there is no
    # need. We just return m instead.
    return m

def listen_and_reply(sock, compute_func):
    while True:
        req = sock.recv()
        sock.send(serialize_rsp(compute_func(req)))

def serialize_rsp(s): return str(s)

def load_dag(sift_root):
     return json.load(open(os.path.join(sift_root, 'sift.json')))

def main():
    sift_root = env_var_or_exit('SIFT_ROOT')
    ipc_root = env_var_or_exit('IPC_ROOT')
    dag = load_dag(sift_root)
    threads = {}
    sockets = []
    node_indexes = sys.argv[1:]
    if len(node_indexes) == 0:
        print 'no nodes to execute'
        return 1
    for i in map(int, node_indexes):
        src = os.path.join(sift_root, dag['dag']['nodes'][i]['implementation']['python'])
        print 'loading ' + src
        m = new_module(i, src)

        # Create nanomsg socket.
        addr = 'ipc://%s/%d.sock'% (ipc_root, i)
        s = Socket(REP)
        s.send_timeout = 2000 # ms
        s.connect(addr)
        print 'connected to ', addr
        sockets.append(s)

        # Launch request handler.
        t = threading.Thread(target=listen_and_reply, args=(s, m.compute))
        t.daemon = True
        t.start()
        threads[i] = t

    try:
        while True:
            time.sleep(1)
            for i, thr in threads.items():
                if not thr.isAlive():
                    raise Exception('thread of node with index %d is dead' % i)
    finally:
        print 'closing sockets'
        for s in sockets: s.close()

if __name__ == '__main__':
    main()
