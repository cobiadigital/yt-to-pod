import sqlite3

dbname = 'instance/ai_blog.sqlite'

with sqlite3.connect(dbname) as con:
    cursor = con.cursor()
    cursor.execute('select sql from sqlite_master')
    for r in cursor.fetchall():
        print(r[0])
    cursor.close()