from threading import Thread, Lock, active_count
import zmq
import time
import sys
import random

TIMEOUT = 5000
PORT = 9090
doneNodes = 0

class Node:
    def __init__(self, pid, port, startElection, numberOfNodes, lock):
        self.pid = pid
        self.port = port
        self.startElection = startElection
        self.numberOfNodes = numberOfNodes
        self.isRunning = True
        self.publishSocket = None
        self.subscribeSocket = None
        self.lock = lock
    
    def start(self):
        port = PORT + self.pid
        context = zmq.Context()
        self.publishSocket = context.socket(zmq.PUB)
        self.publishSocket.bind(f"tcp://127.0.0.1:{port}")

        time.sleep(0.1)

        listenThread = Thread(target=self.listen)
        listenThread.start()

        time.sleep(1)

        if self.startElection:
            print(f"Process {self.pid} publish election message")
            self.publishSocket.send_string(f"ELECTION:{self.pid}:-1")
        
        listenThread.join()
    
    def listen(self):
        context = zmq.Context()
        self.subscribeSocket = context.socket(zmq.SUB)
        self.subscribeSocket.subscribe("ELECTION")
        self.subscribeSocket.subscribe("OK")

        ports = [PORT + i for i in range(self.numberOfNodes) if i != self.pid]

        for port in ports:
            self.subscribeSocket.connect(f"tcp://127.0.0.1:{port}")

        poller = zmq.Poller()
        poller.register(self.subscribeSocket, zmq.POLLIN)
        global doneNodes
        while self.isRunning:
            if doneNodes == self.numberOfNodes-1:
                print(f"--- Process {self.pid} is the new coordinator ---")
                time.sleep(0.1)
                self.isRunning = False
            sockets = dict(poller.poll(timeout=TIMEOUT))
            if self.subscribeSocket in sockets and sockets[self.subscribeSocket] == zmq.POLLIN:
                msg = self.subscribeSocket.recv_string().split(":")
                content = msg[0]
                senderId = int(msg[1])
                toId = int(msg[2])
                if content == "ELECTION":
                    
                    if senderId > self.pid:
                        time.sleep(0.1)
                        print(f"Process {self.pid} disqualified")
                        self.isRunning = False
                    else:
                        self.publishSocket.send_string(f"OK:{self.pid}:{senderId}")
                        if not self.startElection:
                            self.startElection = True
                            time.sleep(0.1)
                            print(f"Process {self.pid} publish election message")
                            self.publishSocket.send_string(f"ELECTION:{self.pid}:{senderId}")
                elif content == "OK":
                    if toId == self.pid:
                        time.sleep(0.1)
                        print(f"Process {self.pid} disqualified")
                        self.isRunning = False
            
        self.lock.acquire()

        local_copy = doneNodes
        local_copy += 1
        time.sleep(0.1)
        doneNodes = local_copy

        # unlock the state
        self.lock.release()

def main(args):
    numberProcesses = int(args[1])
    numberStart = int(args[2])
    
    lock = Lock()
    nodes = []
    threads = []

    pids = [i for i in range(numberProcesses)]
    idsStart = random.sample(pids, numberStart)

    for i in range(numberProcesses):
        node = Node(i, PORT+i, False, numberProcesses, lock)
        nodes.append(node)

    for id in idsStart:
        nodes[id].startElection = True

    for node in nodes:
        t = Thread(target=node.start)
        threads.append(t)
        t.start()

    time.sleep(1)

    for t in threads:
        t.join()
    
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Invalid command line arguments!")
    else:
        main(args=sys.argv)