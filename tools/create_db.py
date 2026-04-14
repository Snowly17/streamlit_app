import sqlite3

conn = sqlite3.connect("charger_data.db")
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS chargers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        address TEXT,
        lat REAL,
        lon REAL,
        type TEXT,
        power INTEGER,
        utilization REAL,
        price REAL,
        available_slots INTEGER,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print("数据库 charger_data.db 和表 chargers 已创建。")