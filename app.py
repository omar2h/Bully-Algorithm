from threading import Thread, Lock, active_count
import zmq
import time

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
            print(f"Process {self.pid} multicast election message")
            time.sleep(0.1)
            self.publishSocket.send_string(f"ELECTION:{self.pid}:-1")
        
        listenThread.join()
    
    def listen(self):
        context = zmq.Context()
        self.subscribeSocket = context.socket(zmq.SUB)
        self.subscribeSocket.subscribe("ELECTION")
        self.subscribeSocket.subscribe("OK")

        # all ports except self
        ports = [PORT + i for i in range(self.numberOfNodes) if i != self.pid]

        # subscribe to all ports except self
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
                            print(f"Process {self.pid} multicast election message")
                            time.sleep(0.1)
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

def main():
    while True:
        try:
            startingIds = []
            numProcesses = int(input("Enter number of processes: "))
            print("Processes: ", end=" ")
            for i in range(numProcesses):
                print(i, end=" ")
            print()
            numStarting = int(input("Enter number of nodes calling for election: "))
            if numStarting > numProcesses:
                raise Exception("Please Enter number less than total number of Processes")
            print(f"\nEnter ids calling for election (range(0, {numProcesses})) : ")
            for i in range(numStarting):
                ele = int(input())
                if ele not in range(numProcesses):
                    raise Exception("Index out of range") 
                startingIds.append(ele)
        except Exception as e:
            print(e)
            continue
        break

    lock = Lock()
    nodes = []
    threads = []

    for i in range(numProcesses):
        node = Node(i, PORT+i, False, numProcesses, lock)
        nodes.append(node)

    for id in startingIds:
        nodes[id].startElection = True

    for node in nodes:
        t = Thread(target=node.start)
        threads.append(t)
        t.start()

    time.sleep(1)

    for t in threads:
        t.join()
    input()
    
if __name__ == "__main__":
    main()