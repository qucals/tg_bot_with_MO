import logging as log
import sqlite3


class Database():
    def __init__(self, db_path) -> None:
        self.db_path = db_path

    def is_user_in_db(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT COUNT(*) FROM users WHERE login=?',
                        (username,))
            data = cur.fetchall()
            con.commit()
            return data[0][0] != 0

    def add_user(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('INSERT INTO users (login) VALUES (?)', (username,))
            con.commit()
            log.info(f'Added new user({username})')

    def get_user_interests(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, interest_id FROM user_interests WHERE user_id=
                    (SELECT users.id FROM users WHERE users.login=?)""", (username,))
            data = cur.fetchall()
            con.commit()
            return data

    def get_no_user_interests(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, name FROM interests WHERE id NOT IN 
                (SELECT interest_id FROM user_interests WHERE user_id=
                (SELECT users.id FROM users WHERE users.login=?))""", (username,))
            data = cur.fetchall()
            con.commit()
            return data
