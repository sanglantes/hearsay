from collections import defaultdict
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score
from sklearn.base import BaseEstimator, TransformerMixin
import database
import numpy as np
import re

def preprocess_remove_garbage(author_message: dict[str, list[str]]) -> defaultdict[str, list[str]]:
    cleaned = defaultdict(list)

    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    quote_pattern = re.compile(r'^[><."]')

    for author, messages in author_message.items():
        for message in messages:
            if (
                url_pattern.search(message) or
                quote_pattern.match(message)
            ): continue
            cleaned[author].append(message)

    return cleaned

class AverageWordLength(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        avg_lengths = []
        for msg in X:
            words = re.findall(r'\b\w+\b', msg)
            avg = np.mean([len(w) for w in words]) if words else 0
            avg_lengths.append([avg])
        return np.array(avg_lengths)

class SentenceLength(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([[len(msg)] for msg in X])
    
class Capitalization(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        caps = []
        for msg in X:
            sentences = re.split(r"[\.?!]", msg)
            cnt = 0
            for s in sentences:
                if s and s[0].isupper():
                    cnt += 1
            caps.append([cnt])
        
        return np.array(caps)


function_word_list = [
    'the', 'which', 'and', 'up', 'nobody', 'of', 'being', 'himself', 'to',
    'would', 'must', 'mine', 'a', 'when', 'another', 'anybody', 'i', 'your', 
    'between', 'till', 'in', 'will', 'might', 'herself', 'you', 'their', 
    'that', 'who', 'someone', 'it', 'some', 'whatever', 'for', 'among', 
    'whom', 'he', 'because', 'while', 'on', 'how', 'each', 'we', 'other', 
    'nor', 'they', 'could', 'be', 'our', 'every', 'most', 'with', 'this', 
    'these', 'shall', 'have', 'than', 'few', 'myself', 'but', 'any', 'though', 
    'themselves', 'as', 'where', 'itself', 'not', 'somebody', 'at', 'what', 'so', 
    'there', 'or', 'its', 'therefore', 'should', 'everybody', 'by', 'from', 'those', 
    'however', 'thus', 'all', 'may', 'everyone', 'she', 'yet', 'whether', 'his', 
    'everything', 'do', 'yourself', 'can', 'if', 'within', 'whose', 'such', 'anyone', 
    'my', 'per', 'her', 'either'
]

def punctuation_tokenizer(text: str) -> list[str]:
    return re.findall(r'\.\.\.|[\?\!]{2,}|[.,;:!?\'"-]', text)

pipeline = Pipeline([
    ("features", FeatureUnion([
        ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,4), lowercase=False)),
        ("fw_freq_dist", CountVectorizer(analyzer="word", vocabulary=function_word_list, lowercase=True)),
        ("punct_freq_dist", CountVectorizer(tokenizer=punctuation_tokenizer, vocabulary=['.', '...', '?', '??', '???', '!', ';', ':', '--', '\''])),
        #("sentence_length", SentenceLength()),
        #("avg_wl", AverageWordLength())
        ("caps", Capitalization())
    ],
    transformer_weights={
        "char_ngrams": 1.0,
        "fw_freq_dist": 1.0,
        "punct_freq_dist": 5.0,
        #"sentence_length": 5.0,
        #"avg_wl": 5.0
        "caps": 5.0
    }
    )),
    #("scaler", StandardScaler(with_mean=False)),
    ("clf", LinearSVC(class_weight="balanced"))
])

author_messages = preprocess_remove_garbage(
    database.get_messages_with_x_plus_messages(150, database.get_db_timestamp("database.db"), "database.db")
)

X, y = [], []
for nick, msgs in author_messages.items():
    for msg in msgs:
        X.append(msg)
        y.append(nick)

pipeline.fit(X, y)

dummy = DummyClassifier(strategy="most_frequent")

y_pred_test = cross_val_predict(pipeline, X, y, cv=10)
y_pred_dummy = cross_val_predict(dummy, X, y, cv=10)

acc_test = accuracy_score(y, y_pred_test)
acc_dummy = accuracy_score(y, y_pred_dummy)

print(acc_test, acc_dummy)
print(f1_score(y, y_pred_test, average="macro"), f1_score(y, y_pred_dummy, average="macro"))

print(pipeline.predict(["The big banks have incredibly, incredibly fast software that is directly connected to the NYSE servers to trade and make split nanosecond decisions. That's so cool"]))