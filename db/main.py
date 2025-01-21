import sqlite3
import json
import sys
DB_PATH = "/app/db/data/conversations.db"

def create_db_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    # Check if table exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation'")
    table_exists = cursor.fetchone() is not None
    print(f"Conversation table already exists: {table_exists}")
    if not table_exists:
        print(f"Creating database at {DB_PATH}")
        conn.execute('CREATE TABLE conversation (id INTEGER PRIMARY KEY AUTOINCREMENT, input TEXT, output TEXT)')
        print("Created conversation table")
    conn.close()

def insert_conversation(input: str, output: str):
    print(f"Inserting conversation into {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO conversation (input, output) VALUES (?, ?)', (input, output))
    conn.commit()
    conn.close()

def get_conversation(id: str):
    print(f"Fetching conversation from {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT input, output FROM conversation WHERE id = ?', (id,))
    conversation = cursor.fetchone()
    conn.close()
    return conversation

def dump_db_to_file(filename: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT * FROM conversation')
    with open(filename, 'w') as f:
        json.dump(cursor.fetchall(), f)
    conn.close()

if __name__ == "__main__":
    print(f"Running {sys.argv[0]} with args {sys.argv[1:]}")

    if len(sys.argv) > 1 and sys.argv[1] == "create_db_if_not_exists":
        create_db_if_not_exists()