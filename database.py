import sqlite3

class Database:
    def __init__(self, path) -> None:
        self.path = path
        self.db = sqlite3.connect(self.path)
        self.cursor = self.db.cursor()

    def is_user_in_db(self, login) -> bool:
        rows = self.cursor.execute(f'SELECT * FROM users WHERE login={login}')
        return len(rows) > 0

    def close(self):
        self.db.commit()
        self.db.close()