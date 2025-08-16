import sqlite3
import os
from joblib import Memory
from collections import defaultdict

memory = Memory("./cache")

DP = "/app/data/database.db"
DB_TIMESTAMP = lambda: int(os.path.getmtime(DP)) // 1000

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DP)

def get_nicks_with_x_plus_messages(x: int) -> list[str]:
    with sqlite3.connect(DP) as conn:
        res = conn.execute("SELECT nick FROM messages GROUP BY nick HAVING COUNT(*) > ?", (x,))
        return [u[0] for u in res]
    
@memory.cache
def get_messages_with_x_plus_messages(x: int, cf: int = 0, DBT: int = DB_TIMESTAMP()) -> dict[str, list[str]]:
    author_message = defaultdict(list)
    
    base_query = """
        SELECT nick, message
        FROM (
            SELECT m.nick, m.message,
                   ROW_NUMBER() OVER (PARTITION BY m.nick ORDER BY m.time DESC) AS rn
            FROM messages m
            JOIN users u ON m.nick = u.nick
            WHERE u.opt = 1
    """

    params = []

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

    base_query += """
        ) t
        JOIN (
            SELECT nick
            FROM messages
            GROUP BY nick
            HAVING COUNT(*) >= ?
        ) eligible ON t.nick = eligible.nick
        WHERE rn <= 8500
    """
    params.append(x)
    
    with sqlite3.connect(DP) as conn:
        res = conn.execute(base_query, params)
        for nick, message in res:
            author_message[nick].append(message)
    
    return author_message

@memory.cache
def get_messages_from_nick(nick: str, DBT: int = DB_TIMESTAMP()) -> list[str]:
    with sqlite3.connect(DP) as conn:
        res = conn.execute("SELECT message FROM messages WHERE nick = ? ORDER BY id DESC LIMIT 10000", (nick,))
        return [msg[0] for msg in res]

def is_nick_eligible(count: int, nick: str) -> bool:
    with sqlite3.connect(DP) as conn:
        res = conn.execute("""SELECT
                           COUNT(*)
                           FROM messages m
                           JOIN users u WHERE u.nick = m.nick
                           AND opt = 1
                           AND m.nick = (?)
                           """, (nick,))
        return int(res.fetchone()[0]) >= count