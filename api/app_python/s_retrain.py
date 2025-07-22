from collections import defaultdict
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.feature_selection import f_classif, SelectKBest
from sklearn.model_selection import cross_val_score, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import TruncatedSVD
import database
import numpy as np
import re
import matplotlib.pyplot as plt
from random import shuffle, seed
from collections import Counter

def preprocess_remove_garbage(author_message: dict[str, list[str]]) -> defaultdict[str, list[str]]:
    cleaned = defaultdict(list)

    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    quote_pattern = re.compile(r'^[><."“!:*]')
    date_quote = re.compile(r'^(?:\[\d{2}:\d{2}:\d{2}\]|\d{2}:\d{2}:\d{2})')

    for author, messages in author_message.items():
        for message in messages:
            if (
                url_pattern.search(message) or
                quote_pattern.match(message) or
                date_quote.match(message)
            ): continue
            cleaned[author].append(message)

    return cleaned


class WordLengthDistribution(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        result = []
        for msg in X:
            dist = [0] * 30
            words = re.findall(r'\b\w+\b', msg)
            for word in words:
                length = min(len(word), 29)
                dist[length] += 1
            result.append(dist)

        return np.array(result)


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
            cntr = 0
            for s in sentences:
                s = s.lstrip()
                if s and s[0].isupper():
                    cntr += 1
            caps.append([cntr])
        
        return np.array(caps)
    

class PerClassTopWordsVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self, top_n=50):
        self.top_n = top_n
        self.vocab_ = []

    def fit(self, X, y):
        class_word_counts = defaultdict(Counter)

        for msg, label in zip(X, y):
            words = re.findall(r'\b\w+\b', msg.lower())
            class_word_counts[label].update(words)

        vocab_set = set()
        for label, counter in class_word_counts.items():
            top_words = [word for word, _ in counter.most_common(self.top_n)]
            vocab_set.update(top_words)

        self.vocab_ = sorted(vocab_set)
        return self

    def transform(self, X):
        vectorizer = CountVectorizer(vocabulary=self.vocab_)
        return vectorizer.transform(X)



function_word_list = [
    'the', 'which', 'and', 'up', 'nobody', 'of', 'being', 'himself', 'to',
    'would', 'must', 'mine', 'a', 'when', 'another', 'anybody', 'i', 'your',
    'till', 'in', 'will', 'might', 'herself', 'you', 'their', 
    'that', 'who', 'someone', 'it', 'some', 'whatever', 'for', 'among', 
    'whom', 'he', 'because', 'while', 'on', 'how', 'each', 'we', 'other', 
    'nor', 'they', 'could', 'be', 'our', 'every', 'most', 'with', 'this', 
    'these', 'shall', 'have', 'than', 'few', 'myself', 'but', 'any', 'though', 
    'themselves', 'as', 'where', 'itself', 'not', 'somebody', 'at', 'what', 'so', 
    'there', 'or', 'its', 'therefore', 'should', 'everybody', 'by', 'from', 'those', 
    'however', 'thus', 'all', 'may', 'everyone', 'she', 'yet', 'whether', 'his', 
    'everything', 'do', 'yourself', 'can', 'if', 'whose', 'such', 'anyone', 
    'my', 'per', 'her', 'either'
] # PREVIEW TESTS HAVE SHOWN INEFFECTIVE. EXPAND OR REMOVE

def punctuation_tokenizer(text: str) -> list[str]:
    return re.findall(r'\.\.\.|[\?\!]{2,}|[.,;:!?\'"-]', text)

def create_pipeline() -> Pipeline:
    pipeline = Pipeline([
        ("features", FeatureUnion([
            ("reduced_tfidf", Pipeline([
                ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,3), lowercase=True)),
                #("sb", SelectKBest(score_func=f_classif, k=1000))
                #("svd", TruncatedSVD(n_components=1000))
            ])),
            #("fw_freq_dist", CountVectorizer(analyzer="word",
             #                                vocabulary=function_word_list,
              #                               lowercase=True)),
            ("punct_freq_dist", CountVectorizer(tokenizer=punctuation_tokenizer,
                                                vocabulary=['.', '...', '?', '???', '!', ';', ':', '\''],
                                                token_pattern=None)),
            #("sentence_length", SentenceLength()),
            ("wl_dist", WordLengthDistribution()),
            ("caps", Capitalization()),
            #("tfw", PerClassTopWordsVectorizer())
        ],
        transformer_weights={
            #"punct_freq_dist": 1,
            #"sentence_length": 5.0,
            #"avg_wl": 5.0
            #"caps": 1
            #"reduced_tfidf": 2.0
        }
        )),
        #("scaler", Normalizer()),
        ("clf", LinearSVC(class_weight="balanced", max_iter=10000))
    ])
    return pipeline


def get_X_y(min_messages: int) -> tuple[list[str], list[str]]:
    author_messages = preprocess_remove_garbage(
        database.get_messages_with_x_plus_messages(min_messages, database.get_db_timestamp())
    )
    X, y = [], []
    cap = min(len(v) for v in author_messages.values()) + 250
    for nick, msgs in author_messages.items():
        shuffle(msgs)
        for msg in msgs[:cap]:
            X.append(msg)
            y.append(nick)
    return X, y


def evaluate_pipeline(pipeline: Pipeline, X: list[str], y: list[str], cv: int = 5) -> tuple[np.ndarray, list[str], float, float]:
    y_test = cross_validate(pipeline, X, y, cv=cv, scoring=["accuracy", "f1_macro"])
    y_pred_test = cross_val_predict(pipeline, X, y, cv=cv) # really annoying to have to run CV twice

    cm = confusion_matrix(y, y_pred_test)

    acc = y_test["test_accuracy"].mean()
    f1 = y_test["test_f1_macro"].mean()

    return cm, pipeline.classes_, acc, f1


def plot_and_save_confusion_matrix(cm: np.ndarray, labels: list[str], filename: str = "cm.png"):
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap="Blues", xticks_rotation=45)
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(filename, dpi=300)

if __name__ == "__main__":
    pipeline = create_pipeline()
    X, y = get_X_y(200)
    pipeline.fit(X, y)
    print(pipeline.named_steps["clf"].classes_)

    c = cross_validate(pipeline, X, y, cv=10, scoring=["accuracy", "f1_macro"])
    print(f"accuracy:\t{c['test_accuracy'].mean()}\nf1:\t{c['test_f1_macro'].mean()}")