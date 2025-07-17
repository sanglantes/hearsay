import sqlite3
import os
from joblib import Memory
from collections import defaultdict
from pprint import pprint

memory = Memory("./cache")

def get_connection(db_path: str = "database.db") -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def get_db_timestamp(db_path: str = "database.db") -> float:
    """
    The purpose of this function is to invalidate cache by checking database updates.
    If the message pool limit is low, this function is generally needless.
    """

    return os.path.getmtime(db_path)

@memory.cache
def get_nicks_with_x_plus_messages(x: int, db_time: float, db_path: str = "database.db") -> list[str]:
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("SELECT nick FROM messages GROUP BY nick HAVING COUNT(nick) > ?", (x,))
        return [u[0] for u in res]
    
@memory.cache
def get_messages_with_x_plus_messages(x: int, db_time: float, db_path: str = "database.db") -> dict[str, list[str]]:
    author_message = defaultdict(list)
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("SELECT nick,message FROM messages WHERE nick IN (SELECT nick FROM messages GROUP BY nick HAVING COUNT(nick) > ?)", (x,))
        for nick, message in res:
            author_message[nick].append(message)
    
    return author_message

db = get_connection()
pprint(get_messages_with_x_plus_messages(150, get_db_timestamp()))