import struct
import sys
import threading
import socket
from dataclasses import dataclass
from db import Database
import time
import queue
import select


@dataclass
class ServerInfo:
    name: str
    ip: str
    port: int
    connected: bool


global shareBuffer


class Client():
    def __init__(self, name):
        # Placeholder Threads
        self.netName = name
        self.servers = []
        self.scanThread = None
        # open database
        self.dbPath = "{}.db".format(self.netName)
        # create new session entry
        db = Database(self.dbPath)
        db.insert("""
            INSERT INTO sessions (starttime)
            VALUES ({})""".format(time.time()))
        # get the current sessions id
        self.sessionID = db.select("""
                                    SELECT MAX (id)
                                    FROM sessions
                                    """)[0][0]
        db.show()

    def startScanning(self):
        self.scanThread = threading.Thread(target=self.scanServers,
                                           name='scanServers')
        self.scanThread.start()
        return self.scanThread

    def addServerToList(self, server, db):
        return db.addDevice(server.name,
                            server.ip,
                            server.port,
                            self.sessionID)

    def printServerList(self):
        db = Database(self.dbPath)
        print(db.select("""
                            SELECT * FROM devices;
                            """))

    def scanServers(self):
        db = Database(self.dbPath)
        message = '{}'.format(self.netName)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = 5000
        sock.bind(('', port))
        group = socket.inet_aton('224.1.1.1')
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # sock.settimeout(5)

        # Thread main loop
        while True:
            try:
                # Waiting for message
                try:
                    data, address = sock.recvfrom(1024)
                except socket.timeout:
                    # Socket timeout
                    print('Socket timeout')
                    break
                except KeyboardInterrupt:
                    # Socket timeout
                    # print('Socket timeout')
                    break
                else:
                    data = data.decode('utf-8')
                    # print('Received message from %s: %s' %
                    #       (address, data))
                    if self.addServerToList(ServerInfo(data,
                                                       address[0],
                                                       0,
                                                       False),
                                            db):
                        sock.sendto(message.encode('utf-8'), address)
                        # Start a thread to share the port
            except Exception as e:
                print('Exception thrown: %s' % e)
                break

    def listenTrigger(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)
        sock.bind(('0.0.0.0', 50000))
        sock.listen(5)
        inputs = [sock]
        outputs = []
        in_queues = {}
        out_queues = {}
        while inputs:
            try:
                readable, writable, exceptional = select.select(
                    inputs, outputs, inputs)
                for s in readable:
                    if s is sock:
                        connection, client_address = s.accept()
                        connection.setblocking(0)
                        inputs.append(connection)
                        in_queues[connection] = queue.Queue()
                        out_queues[connection] = queue.Queue()
                    else:
                        data = s.recv(100)
                        start = round(time.time() * 1000)
                        if data:
                            in_queues[s].put([data, start])
                            if s not in outputs:
                                outputs.append(s)
                        else:
                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            s.close()
                            del in_queues[s]

                for s in writable:
                    try:
                        next_msg = out_queues[s].get_nowait()
                    except queue.Empty:
                        outputs.remove(s)
                    else:
                        s.send(next_msg[0])
                        # End of internal latency
                        print("latency")
                        print(round(time.time() * 1000) - next_msg[1])

                for s in exceptional:
                    inputs.remove(s)
                    if s in outputs:
                        outputs.remove(s)
                    s.close()
                    del in_queues[s]
            except KeyboardInterrupt:
                sock.close()
            for key, q in in_queues.items():
                try:
                    msg = q.get_nowait()
                    # start trigger code
                    print("msg")
                    print(msg)
                    out_queues[key].put([msg[0] +
                                        b'-acc_' +
                                         self.netName.encode('UTF-8'),
                                         round(time.time() * 1000)])

                    # internal Latency until triggering
                    latency = round(time.time() * 1000) - msg[1]
                    print("latency:")
                    print(latency)
                except queue.Empty:
                    pass


def main(clientName):
    c = Client(clientName)
    c.startScanning()
    # while scanThread.is_alive():
    #     pass
    # print()
    # c.printServerList()

    c.listenTrigger()

    pass


if __name__ == '__main__':
    main(sys.argv[1])
