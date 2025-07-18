from collections import defaultdict
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from pprint import pprint
from sklearn.metrics import f1_score
from sklearn.model_selection import cross_val_score
import database
import itertools
import re

def preprocess_remove_noise(author_message: dict[str, list[str]]):
    cleaned = defaultdict(list)

    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    quote_pattern = re.compile(r"^\s*[<>|].*")
    full_quote_pattern = re.compile(r'^".*"$')

    combined_pattern = re.compile(
    r'(https?://\S+|www\.\S+)|(^\s*[<>|].*)|(^".*"$)',
    )

    for author, messages in author_message.items():
        for message in messages:
            if (
                url_pattern.search(message) or
                quote_pattern.match(message) or
                full_quote_pattern.match(message)
            ): continue
            cleaned[author].append(message)

    return dict(cleaned)

def function_word_frequency_distribution(author_message: dict[str, list[str]]):
    return

vect = TfidfVectorizer(analyzer="char", ngram_range=(2,3), lowercase=False)
author_messages = preprocess_remove_noise(database.get_messages_with_x_plus_messages(100, database.get_db_timestamp("database.db"), "database.db"))

messages_chained = itertools.chain.from_iterable(author_messages.values())

X_dtm = vect.fit_transform(messages_chained)

author_map = list(itertools.chain.from_iterable([[nick] * len(author_messages[nick]) for nick in author_messages.keys()]))

clf = LinearSVC(max_iter=2000)

#clf.fit(X_dtm, author_map)

print(cross_val_score(clf, X_dtm, author_map, cv=10, scoring="accuracy").mean())
print(len(author_messages[sorted(author_messages, key=lambda x: len(author_messages[x]), reverse=True)[0]])/sum(len(author_messages[k]) for k in author_messages.keys()))