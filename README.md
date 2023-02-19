# Bully Algorithm

This is a Python implementation of the Bully algorithm using the ZeroMQ library for messaging (publish-subscribe pattern). The algorithm allows for a group of distributed processes to elect a coordinator.

## Prerequisites

- Python 3.x
- ZeroMQ Python library (can be installed via pip)

## Usage

1. Execute command `pip install requirements.txt`
2. Run the script by executing the command python app.py
3. Enter the number of processes that will participate in the election
4. Enter the ids of the nodes that will initiate the election
5. The script will output logs of the election process
6. The script will end when a coordinator has been elected

Or simply run the executable `app.py` in dist folder

## Bully Algorithm Overview

In distributed computing, the bully algorithm is a method for dynamically electing a coordinator or leader from a group of distributed computer processes. The process with the highest process ID number from amongst the non-failed processes is selected as the coordinator.

## How it works

1. When a process notices that the current coordinator is not responding, it starts an election by sending an ELECTION message to all processes.
2. If a process with a higher ID responds, it sends an OK message, indicating that it is still alive. The higher-ID process then starts its own election by sending ELECTION messages to all processes.
3. The process with the highest id is chosen as the new coordinator

## Implementation

```py
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
```

`Node` class represents a process in the distributed system. The class has the process ID, port, startElection boolean, the number of total nodes, publish and subscribe sockets.

```py
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
        self.publishSocket.send_string(f"ELECTION:{self.pid}:-1")

    listenThread.join()
```

The `start` method creates and binds a publish socket using ZeroMQ, starts a listen thread, and sends an `ELECTION` message if the startElection flag is set.

````py
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
            ```
````

The listen method creates a subscribe socket and connects to other processes except self. It subscribe by topic to listen for `ELECTION` and `OK` messages from other nodes in the system.

- If node receives an `ELECTION` message, the node checks whether:
  - if sender's ID is higher than node's id it is disqualified.
  - if sender's ID is lower than node's id, node sends an OK message for the sender.
- If node receives an OK message, the node checks if the message was sent to it and stops listening for messages if it was.

## Example run

```
Enter number of processes: 10
Processes:  0 1 2 3 4 5 6 7 8 9
Enter number of nodes calling for election: 2

Enter ids calling for election (range(0, 10)) :
2
6
Process 2 multicast election message
Process 6 multicast election message
Process 7 multicast election message
Process 4 multicast election message
Process 9 multicast election message
Process 3 multicast election message
Process 5 multicast election message
Process 8 multicast election message
Process 0 disqualified
Process 1 disqualified
Process 2 disqualified
Process 5 disqualified
Process 3 disqualified
Process 7 disqualified
Process 8 disqualified
Process 4 disqualified
Process 6 disqualified
--- Process 9 is the new coordinator ---

```
