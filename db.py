import sqlite3  
  
try:
    conn = sqlite3.connect('authentication.db')
    print('Database opened')
    cur = conn.cursor()

    # Create the 'keys' table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key VARCHAR(50) UNIQUE NOT NULL
        )
    """)

    conn.commit()
    print('Table created')

except sqlite3.Error as e:
    print(f"SQLite error: {e}")

finally:
        # Close the database connection
    if conn:
        conn.close()
        print('Database connection closed')