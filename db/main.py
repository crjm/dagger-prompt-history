import sqlite3
import json
import sys

def create_db():
    conn = sqlite3.connect('conversations.db')
    conn.execute('CREATE TABLE conversation (id INTEGER PRIMARY KEY AUTOINCREMENT, input TEXT, output TEXT)')
    conn.close()

def insert_conversation(input: str, output: str):
    conn = sqlite3.connect('conversations.db')
    conn.execute('INSERT INTO conversation (input, output) VALUES (?, ?)', (input, output))
    conn.commit()
    conn.close()

def get_conversation(id: str):
    conn = sqlite3.connect('conversations.db')
    cursor = conn.execute('SELECT input, output FROM conversation WHERE id = ?', (id,))
    conversation = cursor.fetchone()
    conn.close()
    return conversation

def dump_db_to_file(filename: str):
    conn = sqlite3.connect('conversations.db')
    cursor = conn.execute('SELECT * FROM conversation')
    with open(filename, 'w') as f:
        json.dump(cursor.fetchall(), f)
    conn.close()

create_db()

if __name__ == "__main__":
    command = sys.argv[1]  # "dump_db_to_file"
    filename = sys.argv[2]  # "dump_db.json"
    
    if command == "dump_db_to_file":
        dump_db_to_file(filename)
    else:
        print(f"Invalid command when calling script directly: {command}")
