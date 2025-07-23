import textstat
import database
import re

def preprocess_remove_garbage(author_message: list[str]) -> list[str]:
    cleaned = []

    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    quote_pattern = re.compile(r'^[><."“!:*\[]')
    for message in author_message:
        if (
            url_pattern.search(message) or
            quote_pattern.match(message)
        ): continue
        cleaned.append(message)

    return cleaned

def flesch_score(nick: str) -> float:
    author_text = preprocess_remove_garbage(database.get_messages_from_nick(nick, database.get_db_timestamp()))
    author_text = '. '.join(author_text)
    flesch_result: float = textstat.flesch_reading_ease(author_text)
    
    return flesch_result