import logging as log
from os import name
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
            return data[0][0] != 0

    def is_admin(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT COUNT(*) FROM admins WHERE login=?',
                        (username,))
            data = cur.fetchall()
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

    def remove_user_rating(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""DELETE FROM rating WHERE user_id=(
                SELECT id from users WHERE login=?)""", (username,))
            con.commit()

    def get_user_interests(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, interest_id FROM user_interests WHERE user_id=
                    (SELECT users.id FROM users WHERE users.login=?)""", (username,))
            data = cur.fetchall()
            return data

    def get_no_user_interests(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id, name FROM interests WHERE id NOT IN 
                (SELECT interest_id FROM user_interests WHERE user_id=
                (SELECT users.id FROM users WHERE users.login=?))""", (username,))
            data = cur.fetchall()
            return data

    def get_all_interests(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT * FROM interests')
            data = cur.fetchall()
            return data

    def get_user_id(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT id FROM users WHERE login=?', (username,))
            data = cur.fetchall()
            return data[0][0]

    def get_info(self, doc_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                'SELECT (name, description) FROM docs WHERE id=?', (doc_id,))
            data = cur.fetchall()
            return data[0]

    def get_all_rating_info(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                'SELECT user_id, doc_id, rate FROM rating ORDER BY user_id')
            data = cur.fetchall()
            return data

    def get_rating_matrix(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT id FROM docs')
            docs_id = cur.fetchall()

            cur.execute('SELECT id FROM users')
            users_id = cur.fetchall()

            cur.execute('SELECT * FROM rating')
            rating = cur.fetchall()

            matrix = {}
            for user_id in users_id:
                matrix[user_id[0]] = {doc_id[0]: 0 for doc_id in docs_id}

            for mark in rating:
                matrix[mark[2]][mark[1]] = mark[3]

            return matrix

    def get_unappreciated_docs(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id
                FROM docs
                WHERE id NOT IN (
                    SELECT doc_id
                    FROM rating
                    WHERE user_id=(
                        SELECT id
                        FROM users
                        WHERE login=?
                    )
                )
            """, (username,))
            data = cur.fetchall()
            result = [d[0] for d in data]
            return result

    def get_appreciated_docs(self, username):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT id
                FROM docs
                WHERE id IN (
                    SELECT doc_id
                    FROM rating
                    WHERE user_id=(
                        SELECT id
                        FROM users
                        WHERE login=?
                    )
                )
            """, (username,))
            data = cur.fetchall()
            result = [d[0] for d in data]
            return result

    def get_doc(self, doc_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                'SELECT name, description FROM docs WHERE id=?', (doc_id,))
            data = cur.fetchall()
            return data[0]

    def get_similarity_interest(self, username, doc_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT COUNT(*)
                FROM tegs
                WHERE interest_id IN (
                    SELECT interest_id 
                    FROM user_interests
                    WHERE user_id=(
                        SELECT id FROM users WHERE login=?
                    )
                ) AND doc_id=?
            """, (username, doc_id))
            data = cur.fetchall()
            return data[0][0]

    def get_all_docs(self):
        result = []

        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT id, name FROM docs')
            data = cur.fetchall()

            for idx, name in data:
                cur.execute('SELECT name FROM interests WHERE id IN (SELECT interest_id FROM tegs WHERE doc_id=?)', (idx,))
                tegs = cur.fetchall()
                _tegs = [t[0] for t in tegs]
                result.append((idx, name, _tegs))

        return result

    def get_doc_for_admin(self, doc_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT * FROM docs WHERE id=?', (doc_id,))
            data = cur.fetchall()
            return data[0]

    def get_interest_for_admin(self, interest_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT * FROM interests WHERE id=?', (interest_id,))
            data = cur.fetchall()
            return data[0]

    def remove_doc(self, doc_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('DELETE FROM docs WHERE id=?', (doc_id,))
            con.commit()

    def remove_interest(self, interest_id):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('DELETE FROM interests WHERE id=?', (interest_id,))
            con.commit()

    def add_doc(self, name, desc):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                'INSERT OR REPLACE INTO docs (name, description) VALUES (?, ?)', (name, desc,))
            con.commit()

    def add_interest(self, name):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('INSERT OR REPLACE INTO interests (name) VALUES (?)', (name,))
            con.commit()

    def set_rating_info(self, username, doc_id, rating):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO rating (doc_id, user_id, rate, is_shown) VALUES (
                    ?,
                    (SELECT id FROM users u WHERE u.login=?),
                    ?,
                    0)
                """, (str(doc_id), str(username), str(rating)))
            con.commit()
