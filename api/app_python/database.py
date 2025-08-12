import sqlite3
import os
from joblib import Memory
from collections import defaultdict

memory = Memory("./cache")

dp = "/app/data/database.db"

def get_connection(db_path: str = dp) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def get_db_timestamp(db_path: str = dp) -> int:
    """
    The purpose of this function is to invalidate cache by checking database updates.
    If the message pool limit is low, this function is generally needless.
    
    Heavy(ier) functions will use get_db_timestamp if and only if it uses @memory.cache
    """

    return int(os.path.getmtime(db_path)) // 1000 # We add a 1000 second leniency

def get_nicks_with_x_plus_messages(x: int, db_path: str = dp) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("SELECT nick FROM messages GROUP BY nick HAVING COUNT(*) > ?", (x,))
        return [u[0] for u in res]
    
@memory.cache
def get_messages_with_x_plus_messages(x: int, cf: int, db_path: str = dp) -> dict[str, list[str]]:
    author_message = defaultdict(list)
    
    base_query = """
        SELECT m.nick, m.message 
        FROM messages m
        JOIN users u ON m.nick = u.nick
        WHERE u.opt = 1
          AND m.nick IN (
            SELECT nick
            FROM messages
            GROUP BY nick
            HAVING COUNT(*) > ?
          )
    """
    
    params = [x]
    
    if cf > 0:
        base_query += """
          AND m.nick IN (
            SELECT nick
            FROM messages
            GROUP BY nick
            HAVING MAX(time) > datetime('now', '-' || ? || ' days')
          )
        """
        params.append(cf)
    
    with sqlite3.connect(db_path) as conn:
        res = conn.execute(base_query, params)
        for nick, message in res:
            author_message[nick].append(message)
    
    return author_message

@memory.cache
def get_messages_from_nick(nick: str, db_time: int, db_path: str = dp) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("SELECT message FROM messages WHERE nick = ? ORDER BY id DESC LIMIT 10000", (nick,))
        return [msg[0] for msg in res]

def is_nick_eligible(count: int, nick: str, db_path: str = dp) -> bool:
    with sqlite3.connect(db_path) as conn:
        res = conn.execute("""SELECT
                           COUNT(*)
                           FROM messages m
                           JOIN users u WHERE u.nick = m.nick
                           AND opt = 1
                           AND m.nick = (?)
                           """, (nick,))
        return int(res.fetchone()[0]) >= count