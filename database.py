# database.py
import sqlite3

DATABASE_NAME = 'celestium.db'

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    # Table to store quiz results for AI recommendations
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database Initialized! A 'celestium.db' file has been created.")