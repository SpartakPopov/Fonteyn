# database creation

import sqlite3
from db import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        username TEXT UNIQUE NOT NULL PRIMARY KEY,
        names TEXT NOT NULL,
        email TEXT NOT NULL,
        position TEXT NOT NULL,
        password TEXT NOT NULL
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_users (
        username TEXT UNIQUE NOT NULL PRIMARY KEY,
        names TEXT NOT NULL,
        email TEXT NOT NULL,
        position TEXT NOT NULL,
        password TEXT NOT NULL
    );
    ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
