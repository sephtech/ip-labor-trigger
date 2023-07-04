import threading
import util
import socket
import time
from dataclasses import dataclass


@dataclass
class ClientInfo:
    name: str
    ip: str
    sendPort: int
    recvPort: int
    connected: bool


@dataclass
class SharedResource:
    clients: list
    flag: str


global share


class Server():
    def __init__(self, name):
        # Placeholder Threads
        self.netName = name
        self.clients = []
        self.scanThread = None
        self.shareThread = None
        # self.sendThread = None
        # self.recvThread = None

    def shareInfo(self):
        global share
        while self.scanThread.is_alive():
            if share.flag == 'ready':
                share.flag = 'share'
            time.sleep(0.1)
            if share.flag == 'share':
                print('Share')
                share.clients = self.clients
                share.flag = 'freeShare'

    def startScanning(self):
        self.scanThread = threading.Thread(target=self.scanClients,
                                           name='scanClients')
        self.scanThread.start()
        self.shareThread = threading.Thread(target=self.shareInfo,
                                            name='shareInfo')
        self.shareThread.start()
        return self.scanThread

    def addClientToList(self, client):
        global share
        checkTup = (client.name, client.ip)
        if checkTup not in [(c.name, c.ip) for c in self.clients]:
            self.clients.append(client)
            share.flag = 'ready'

    def printClientList(self):
        for c in self.clients:
            print(c)

    def scanClients(self):
        message = '{},{},{}'.format(self.netName,
                                    util.getFreePort(),
                                    util.getFreePort())
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        2)
        # Thread main loop
        counter = 0
        while counter < 10:
            try:
                sock.sendto(message.encode('utf-8'),
                            ('224.1.1.1', 5000))
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
                        data = data.split(',')
                        self.addClientToList(ClientInfo(data[0],
                                                        address[0],
                                                        data[1],
                                                        data[2],
                                                        False))
            except Exception as e:
                print('Exception thrown: %s' % e)
                break
            counter += 1


def main():
    sharedClients = []
    sharedFlag = 'free'
    global share
    share = SharedResource(sharedClients, sharedFlag)
    s = Server('Server')
    scan_thread = s.startScanning()
    list = []
    while scan_thread.is_alive():
        if share.flag == 'freeShare':
            share.flag = 'main'
        time.sleep(0.1)
        if share.flag == 'main':
            print('Main')
            one = set([(c.name, c.ip) for c in share.clients])
            two = set([(c.name, c.ip) for c in list])
            if one != two:
                list = share.clients.copy()
                print(list)
            share.flag = 'free'
    # print(list)
    # print(share.clients)
    print(list)
    s.printClientList()
    pass


if __name__ == '__main__':
    main()
