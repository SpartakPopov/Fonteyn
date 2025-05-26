import sqlite3
from passlib.hash import bcrypt

DB_NAME = "hrm.db"

#file with all database functions

def register_employee(username, names, email, position, password):
    hashed_password = bcrypt.hash(password)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO pending_users (username, names, email, position, password)
        VALUES (?,?,?,?,?)

        
        ''', (username, names, email,position, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def all_employees():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, names, email, position FROM employees")
    rows = cursor.fetchall()
    conn.close()
    return rows


def edit_employee(username, names, email, position):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE employees
        SET names = ?, email = ?, position = ?
        WHERE username = ?
    ''', (names, email, position, username))
    conn.commit()
    conn.close()


def get_password(username):
    conn = sqlite3.connect(DB_NAME)
    cursor= conn.cursor()
    cursor.execute("SELECT password FROM employees WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None



def delete_employee(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE username = ?", (username,))
    conn.commit()
    conn.close()


def get_pending_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, names, email, position FROM pending_users")
    pending_emps = cursor.fetchall()
    conn.close()
    return pending_emps




def approve_pending_user(username_to_approve: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT username, names, email, position, password FROM pending_users WHERE username = ?", (username_to_approve,))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return False  

    cursor.execute('''
        INSERT INTO employees (username, names, email, position, password)
        VALUES (?, ?, ?, ?, ?)
    ''', (user[0], user[1], user[2], user[3], user[4]))

    cursor.execute("DELETE FROM pending_users WHERE username = ?", (username_to_approve,))

    conn.commit()
    conn.close()
    return True


def reject_pending_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_users WHERE username = ?", (username,))
    conn.commit()
    conn.close()