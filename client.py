import struct
import sys
import threading
import socket
from dataclasses import dataclass


@dataclass
class ServerInfo:
    name: str
    ip: str
    sendPort: int
    recvPort: int
    connected: bool


# @dataclass
# class SharedResource:
#     servers: list
#     flag: str


global shareBuffer


class Client():
    def __init__(self, name):
        # Placeholder Threads
        self.netName = name
        self.servers = []
        self.scanThread = None

    def startScanning(self):
        self.scanThread = threading.Thread(target=self.scanServers,
                                           name='scanServers')
        self.scanThread.start()
        return self.scanThread

    def addServerToList(self, server):
        global shareBuffer
        checkTup = (server.name, server.ip)
        if checkTup not in [(s.name, s.ip) for s in self.servers]:
            self.servers.append(server)
            shareBuffer.append(server)

    def printServerList(self):
        for s in self.servers:
            print(s)

    def scanServers(self):
        message = '{}'.format(self.netName)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = 5000
        while port < 5050:
            try:
                sock.bind(('', port))
                break
            except Exception:
                port += 1
        group = socket.inet_aton('224.1.1.1')
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(5)

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
                else:
                    data = data.decode('utf-8')
                    # print('Received response from %s: %s' %
                    #       (address, data))
                    self.addServerToList(ServerInfo(data,
                                                    address[0],
                                                    0,
                                                    0,
                                                    False))
                    sock.sendto(message.encode('utf-8'), address)
            except Exception as e:
                print('Exception thrown: %s' % e)
                break


def main(clientName):
    global shareBuffer
    shareBuffer = []
    c = Client(clientName)
    scanThread = c.startScanning()
    list = []
    while scanThread.is_alive():
        try:
            list.append(shareBuffer.pop())
            # print(list)
        except Exception:
            pass
    print()
    print(list)
    print()
    c.printServerList()
    pass


if __name__ == '__main__':
    main(sys.argv[1])
