import sqlite3

con = sqlite3.connect("test.db")

cur = con.cursor()

# cur.execute("""CREATE TABLE IF NOT EXISTS table1 (
#             id INTEGER NOT NULL PRIMARY KEY,
#             name,
#             number)""")

cur.execute("DROP TABLE IF EXISTS table1")

# cur.execute("""INSERT INTO table1 (name, number)
#             VALUES ("Florian", 25)""")
# con.commit()


res = cur.execute("SELECT * FROM table1")
print(res.fetchall())
