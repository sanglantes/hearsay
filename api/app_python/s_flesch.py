import textstat
import database

def flesch_score(nick: str) -> float:
    author_text = database.get_messages_from_nick(nick, database.get_db_timestamp())
    author_text = '. '.join(author_text)
    flesch_result: float = textstat.flesch_reading_ease(author_text)
    
    return flesch_result