import sqlite3

conn = sqlite3.connect('banco.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL
)
''')

cursor.execute(
    'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
    (nome, email, senha)
)

conn.commit()
conn.close()
