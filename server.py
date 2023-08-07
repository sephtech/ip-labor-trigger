import sys
import threading
import socket
from dataclasses import dataclass
from db import Database


@dataclass
class ClientInfo:
    name: str
    ip: str
    sendPort: int
    recvPort: int
    connected: bool


global shareBuffer


class Server():
    def __init__(self, name):
        # Placeholder Threads
        self.netName = name
        self.clients = []
        self.scanThread = None
        self.shareThread = None
        # self.sendThread = None
        # self.recvThread = None'
        self.db = Database()
        self.db.show()

    def startScanning(self):
        self.scanThread = threading.Thread(target=self.scanClients,
                                           name='scanClients')
        self.scanThread.start()
        return self.scanThread

    def addClientToList(self, client, db):
        # Wiederholter INSERT Befehl an Datenbank
        db.addDevice(client.name, client.ip, 0)

        # Check in Liste vielleicht schneller?
        # global shareBuffer
        # checkTup = (client.name, client.ip)
        # if checkTup not in [(c.name, c.ip) for c in self.clients]:
        #     self.clients.append(client)
        #     shareBuffer.append(client)

    def printClientList(self):
        db = Database()
        print(db.select("""
                             SELECT * FROM devices;
                             """))
        # for c in self.clients:
        #     print(c)

    def scanClients(self):
        db = Database()
        message = '{}'.format(self.netName)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        2)
        # Thread main loop
        counter = 0
        while counter < 10:
            try:
                port = 5000
                for port in range(5000, 5050):
                    sock.sendto(message.encode('utf-8'),
                                ('224.1.1.1', port))
                # Receiving loop
                while True:
                    try:
                        # waiting for message
                        # print('Waiting for message')
                        data, address = sock.recvfrom(32)
                    except socket.timeout:
                        # Socket timeout, no new messages
                        # print('Socket timeout')
                        break
                    else:
                        data = data.decode('utf-8')
                        # print('Received response from %s: %s' %
                        #       (address, data))
                        self.addClientToList(ClientInfo(data,
                                                        address[0],
                                                        0,
                                                        0,
                                                        False),
                                             db)
            except Exception as e:
                print('Exception thrown: %s' % e)
                break
            counter += 1


def main(serverName):
    global shareBuffer
    shareBuffer = []
    s = Server(serverName)
    scan_thread = s.startScanning()
    list = []
    while scan_thread.is_alive():
        try:
            list.append(shareBuffer.pop())
            # print(list)
        except Exception:
            pass
    print()
    print(list)
    print()
    s.printClientList()

    pass


if __name__ == '__main__':
    # print(f"Arg count: {len(sys.argv)}")
    # for i, arg in enumerate(sys.argv):
    #     print(f"Argument {i:>6}: {arg}")
    main(sys.argv[1])
