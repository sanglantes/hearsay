import database

def sentiment_over_many_messages(nick: str):
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    
    analyzer = SentimentIntensityAnalyzer()

    msgs = database.get_messages_from_nick(nick)
    average_compound_score = sum(analyzer.polarity_scores(v)["compound"] for v in msgs)/len(msgs)

    return average_compound_score