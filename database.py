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

    def add_user_interest(self, username, interest_id):
        user_id = self.get_user_id(username)

        user_interest = self.get_user_interests(username)
        for _, id in user_interest:
            if interest_id == id:
                return False

        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO user_interests (user_id, interest_id) VALUES (?, ?)', (str(user_id), str(interest_id)))
            con.commit()
            return True

    def remove_all_interests(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                DELETE FROM user_interests WHERE user_id=(
                    SELECT id from users WHERE login=?)""", (username,))
            con.commit()

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

    def get_all_interests(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT * FROM interests')
            data = cur.fetchall()
            con.commit()
            return data

    def get_user_id(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT id FROM users WHERE login=?', (username,))
            data = cur.fetchall()
            con.commit()
            return data[0][0]
