import sqlite3
from datetime import datetime

def date_time():
    time = datetime.now()
    return time.strftime("%H:%M:%S"),time.strftime("%d/%m/%Y")

class KeysDatabase:

    def __init__(self,db):

        # Ensure all parameters received
        if db:
            self.conn=sqlite3.connect(db,timeout=10)
            self.cur=self.conn.cursor()
            self.cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username text, hash text)")
            self.cur.execute("CREATE TABLE IF NOT EXISTS list (id INTEGER PRIMARY KEY, user_id INTEGER, app text,username text, key text)")
            self.conn.commit()

        # Error - missing info
        else:
            return -2

    def insert_user(self ,username = "" ,_hash = "" ):

        # Ensure all parameters received
        if username and _hash:
            self.cur.execute("INSERT INTO users VALUES (NULL,?,?)",(username, _hash))
            self.conn.commit()

        # Error - missing info
        else:
            return -2

    def insert_key(self, user_id = "", app = ""  ,username = "", key = ""):

        # Ensure all parameters received
        if user_id and app and username and key:
            self.cur.execute("INSERT INTO list VALUES (NULL,?,?,?,?)",(user_id, app,username, key))
            self.conn.commit()

        # Error - missing info
        else:
            return -2

    #Need to be changed
    def search_user(self, username = "", user_id = ""):

        # Ensure all parameters received
        if username:
            self.cur.execute("SELECT * FROM users WHERE username = ?",(username,))
            rows=self.cur.fetchall()
            return rows

        elif user_id:
            self.cur.execute("SELECT * FROM users WHERE id = ?",(user_id,))
            rows=self.cur.fetchall()
            return rows

        # Error - missing info
        else:
            return -2

    def search_key(self, user_id = "", app = "", username=""):

        # Ensure all parameters received
        if user_id and app and username:
            self.cur.execute("SELECT * FROM list WHERE user_id = ? AND app = ? AND username = ?",(user_id,app,username))
            rows=self.cur.fetchall()
            return rows

        # Error - missing info
        else:
            return -2

    def delete_key(self, user_id = "", app = "", username = ""):

        # Ensure all parameters received
        if user_id and app and username:
            self.cur.execute("DELETE FROM list WHERE user_id = ? AND app = ? AND username = ?",(user_id, app,username))
            self.conn.commit()

        # Error - missing info
        else:
            return -2

    def update_key(self, user_id = "", app = "", username = "", key = ""):

        # Ensure all parameters received
        if user_id and app and username and key:
            self.cur.execute("UPDATE list SET key = ? WHERE user_id = ? AND app = ? AND username = ?",(key, user_id, app, username))
            self.conn.commit()

        # Error - missing info
        else:
            return -2

    def update_user(self, user_id = "", key = ""):
        # Ensure all parameters received
        if user_id and key:
            self.cur.execute("UPDATE users SET hash = ? WHERE id = ?",(key, user_id))
            self.conn.commit()
            return 0
            
        # Error - missing info
        else:
            return -1

    def __del__(self):
        self.conn.close()


class HashDatabase:

    def __init__(self,db):
        # Ensure all parameters received
        if db:
            self.conn=sqlite3.connect(db,timeout=10)
            self.cur=self.conn.cursor()
            self.cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username text, hash text)")
            self.cur.execute("CREATE TABLE IF NOT EXISTS list (id INTEGER PRIMARY KEY, user_id INTEGER, app text,username text, hash text, comment text, date_mod date, time_mod time)")
            self.conn.commit()
        
        # Error - missing info
        else:
            return -1

    def insert_user(self ,username = "" ,_hash = "" ):
        # Ensure all parameters received
        if username and _hash:
            self.cur.execute("INSERT INTO users VALUES (NULL,?,?)",(username, _hash))
            self.conn.commit()

        # Error - missing info
        else:
            return -1

    def insert_hash(self, user_id = "", app = "",username = "", _hash = "", comment = ""):
        # Ensure all parameters received
        if user_id and app and username and _hash and comment:
            [time, date] = date_time()
            self.cur.execute("INSERT INTO list VALUES (NULL,?,?,?,?,?,?,?)",(user_id,app ,username, _hash,comment,date,time))
            self.conn.commit()

        # Error - missing info
        else:
            return -1


    def search_user(self, username = "", user_id = ""):
        # Ensure all parameters received
        if username:
            self.cur.execute("SELECT * FROM users WHERE username = ?",(username,))
            rows=self.cur.fetchall()
            return rows

        elif user_id:
            self.cur.execute("SELECT * FROM users WHERE id = ?",(user_id,))
            rows=self.cur.fetchall()
            return rows
        # Error - missing info
        else:
            return -1

    def search_hash(self, user_id = "", app = "", username = ""):
        #Ensure user_id was received
        if user_id:
            app = app+"%"

            # Empty
            if not username:
                self.cur.execute("SELECT * FROM list WHERE user_id = ? AND (app LIKE ?)",(user_id, app))    
            else:
                username = username +"%"
                self.cur.execute("SELECT * FROM list WHERE user_id = ? AND (app LIKE ? AND username LIKE ?)",(user_id, app, username))
            rows=self.cur.fetchall()
            return rows
        
        # Error - missing info
        return -1


    def delete_hash(self, user_id = "", app = "", username = ""):
        
        # Ensure all parameters received
        if user_id and app and username:
            self.cur.execute("DELETE FROM list WHERE user_id = ? AND username = ? AND app = ?",(user_id, username, app))
            self.conn.commit() 
        
        # Error - missing info
        else:
            return -1

        return 0

    def update_hash(self, user_id = "" ,app = "" ,username = "" , _hash = "", comment = ""):

        # Ensure all parameters received
        
        if username and _hash and app and user_id and comment:
            [time, date] = date_time()
            self.cur.execute("UPDATE list SET hash = ?, comment = ? ,time_mod = ?, date_mod = ? WHERE user_id = ? AND app = ? AND username = ?",
                                                                                        (_hash,comment,time, date, user_id ,app, username))
            self.conn.commit()
        
        # Error - missing info
        else:
            return -1

    def update_user(self, user_id = "", ha = ""):
        # Ensure all parameters received
        if user_id and ha:
            self.cur.execute("UPDATE users SET hash = ? WHERE id = ?",(ha, user_id))
            self.conn.commit()
            return 0

        # Error - missing info
        else:
            return -1

    def update_comment(self, user_id = "", app = "", username = "", comment = ""):
        if username and  app and comment:
            self.cur.execute("UPDATE list SET comment = ? WHERE user_id = ? AND app = ? AND username = ?",(comment, user_id ,app, username))
            self.conn.commit()
        else:
            return -1

    def view(self, user_id = ""):
        if user_id:
            self.cur.execute("SELECT * FROM list WHERE user_id = ?", (user_id,))
            rows=self.cur.fetchall()
            return rows
        else:
            return -1

    def __del__(self):
        self.conn.close()

# keys = HashDatabase("Hash.db")
# print(keys.search_hash(1,"dolingo"))
# keys.insert_user("av", "saaa0")
# [time,date] = date_time()
# keys.insert_hash(1,"dolingo","lll", "dsd9io",date,time)
# print(keys.delete_hash(1,"dolingo","Hello"))
# print(keys.search_hash(1,"dolingo"))
# keys.update_hash(1,"dolingo","lll")
# print(keys.search_hash(1,"dolingo"))