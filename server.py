import sys
import threading
import socket
from dataclasses import dataclass
from db import Database
import time


@dataclass
class ClientInfo:
    name: str
    ip: str
    port: int
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
        # self.recvThread = None
        # open database
        self.dbPath = ".\\database\\{}.db".format(self.netName)
        # create new session entry
        db = Database(self.dbPath)
        db.insert(
            """
            INSERT INTO sessions (starttime)
            VALUES ({})""".format(time.time()))
        # get the current sessions id
        self.sessionID = db.select("""
                                SELECT MAX(id)
                                FROM sessions
                                """)[0][0]
        db.show()

    def startScanning(self):
        self.scanThread = threading.Thread(target=self.scanClients,
                                           name='scanClients')
        self.scanThread.start()
        return self.scanThread

    def addClientToList(self, client, db):
        # Einfügen in Datenbank
        db.addDevice(client.name, client.ip, client.port, self.sessionID)

    def printClientList(self):
        db = Database(self.dbPath)
        print(db.select("""
                             SELECT * FROM devices;
                             """))

    def scanClients(self):
        db = Database(self.dbPath)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        2)
        # Thread main loop
        counter = 0
        message = '{}'.format(self.netName)
        while counter < 10:
            try:
                port = 5000
                # for port in range(5000, 5050):
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
                                                        False),
                                             db)
                        # Start a thread to share the port

            except Exception as e:
                print('Exception thrown: %s' % e)
                break
            counter += 1

    def sharePort():
        pass

    def issueTrigger(self, text):
        thread = threading.Thread(target=self.triggerThread,
                                  args=(text,))
        thread.start()
        return thread

    def triggerThread(self, text):
        start = round(time.time() * 1000)
        db = Database(self.dbPath)
        statement = """
                INSERT INTO triggers (text, issuetime, sessionID)
                VALUES ('{}', {}, {})
                """.format(text, time.time(), self.sessionID)
        db.insert(statement)
        id = db.select("""
                    SELECT MAX(id)
                    FROM triggers
                    """)[0][0]

        clientList = db.select("""SELECT *
                               FROM devices
                               WHERE sessionID = {}
                               """.format(self.sessionID))

        # Send trigger message
        port = 50000
        triggerList = []
        for client in clientList:
            t = threading.Thread(target=self.sendTrigger,
                                 args=(text, (client[2], port), ))
            t.start()
            triggerList.append(t)

        # check if there are still active triggers
        while len(triggerList) > 0:
            for t in triggerList:
                if not t.is_alive():
                    triggerList.remove(t)

        # calculate latency and add to trigger database entry
        latency = round(time.time() * 1000) - start
        print(latency)
        statement = """UPDATE triggers
                SET latency={}
                WHERE id = {};
                """.format(latency, id)
        db.insert(statement)

    def sendTrigger(self, text, clientinfo):
        start = round(time.time() * 1000)
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(clientinfo)
        print(round(time.time() * 1000) - start)
        sock.send(text.encode('UTF-8'))
        print(round(time.time() * 1000) - start)
        sock.recv(100)
        print(round(time.time() * 1000) - start)


def main(serverName):
    s = Server(serverName)
    scanThread = s.startScanning()
    while scanThread.is_alive():
        pass
    print()
    s.printClientList()

    print('Issue triggers')
    # triggerList = []
    # for i in range(1, 20):
    #     triggerList.append(s.issueTrigger("{} Triggertext".format(i)))
    #     time.sleep(3)

    # while len(triggerList) > 0:
    #     for t in triggerList:
    #         if not t.is_alive():
    #             triggerList.remove(t)
    t = s.issueTrigger("{} Triggertext".format(1))
    while t.is_alive():
        pass


if __name__ == '__main__':
    # print(f"Arg count: {len(sys.argv)}")
    # for i, arg in enumerate(sys.argv):
    #     print(f"Argument {i:>6}: {arg}")
    main(sys.argv[1])
