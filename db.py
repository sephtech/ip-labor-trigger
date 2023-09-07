import sqlite3


class Database():
    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.createTables()

    def addDevice(self, device_Name, device_IP, device_Port, sessionID):
        statement = """
            INSERT INTO devices (name, ip, port, sessionID)
            VALUES ('{}', '{}', {}, {})
        """.format(device_Name, device_IP, device_Port, sessionID)
        # print(statement)
        try:
            self.insert(statement)
            return True
        except Exception:
            return False

    def getDevice(self, device_ID):
        statement = """SELECT FROM devices WHERE device_ID = {};""".format(
            device_ID)
        return self.select(statement)

    def show(self):
        statement = """SELECT name FROM sqlite_master WHERE type='table';"""
        for res in self.select(statement):
            print("________ " + res[0] + " ________")
            for entry in self.select("""SELECT * FROM {}""".format(res[0])):
                print(entry)

    def insert(self, statement):
        self.cur.execute(statement)
        self.con.commit()

    def select(self, statement):
        res = self.cur.execute(statement)
        return res.fetchall()

    def createTables(self):
        statements = [
            """
        CREATE TABLE IF NOT EXISTS
            sessions (
                id INTEGER NOT NULL PRIMARY KEY,
                starttime DATETIME NOT NULL);
        """,
            """
        CREATE TABLE IF NOT EXISTS
            triggers (
                id INTEGER NOT NULL PRIMARY KEY,
                text TEXT NOT NULL,
                issuetime DATETIME NOT NULL,
                latency INTEGER,
                sessionID INTEGER NOT NULL,
                FOREIGN KEY (sessionID) REFERENCES sessions (id));
        """,
            """
        CREATE TABLE IF NOT EXISTS
            devices (
                id INTEGER NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                ip TEXT NOT NULL,
                port INTEGER,
                sessionID INTEGER NOT NULL,
                UNIQUE (name, ip, sessionID),
                FOREIGN KEY (sessionID) REFERENCES sessions (id));
        """,
            """
        CREATE TABLE IF NOT EXISTS
            networkLatency (
                id INTEGER NOT NULL PRIMARY KEY,
                triggerID INTEGER NOT NULL,
                deviceID DATETIME NOT NULL,
                time INTEGER NOT NULL,
                FOREIGN KEY (triggerID) REFERENCES triggers (id),
                FOREIGN KEY (deviceID) REFERENCES devices (id));
        """,
            """
        CREATE TABLE IF NOT EXISTS
            internalLatency (
                id INTEGER NOT NULL PRIMARY KEY,
                triggerID INTEGER NOT NULL,
                deviceID DATETIME NOT NULL,
                time INTEGER NOT NULL,
                FOREIGN KEY (triggerID) REFERENCES triggers (id),
                FOREIGN KEY (deviceID) REFERENCES devices (id));
        """,
            """
        CREATE TABLE IF NOT EXISTS
            logs(
                id INTEGER NOT NULL PRIMARY KEY,
                text TEXT NOT NULL,
                issuetime datetime NOT NULL,
                sessionID INTEGER NOT NULL,
                FOREIGN KEY (sessionID) REFERENCES sessions (id));
        """]
        for statement in statements:
            self.cur.execute(statement)
