import sqlite3
con = sqlite3.connect('Book.db')

c = con.cursor()

c.execute("SELECT num FROM Books")

print(c.fetchall())

c.close()
con.close()