from collections import defaultdict
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.feature_selection import f_classif, SelectKBest
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import TruncatedSVD
import database
import numpy as np
import re
import matplotlib.pyplot as plt


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
            cntr = 0
            for s in sentences:
                s = s.lstrip()
                if s and s[0].isupper():
                    cntr += 1
            caps.append([cntr])
        
        return np.array(caps)


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
]


def punctuation_tokenizer(text: str) -> list[str]:
    return re.findall(r'\.\.\.|[\?\!]{2,}|[.,;:!?\'"-]', text)


def create_pipeline() -> Pipeline:
    pipeline = Pipeline([
        ("features", FeatureUnion([
            ("reduced_tfidf", Pipeline([
                ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,4), lowercase=False)),
                #("sb", SelectKBest(score_func=f_classif, k=500)) # Faster but reduces performance
                #("svd", TruncatedSVD(n_components=3000)) TOO SLOW
            ])),
            ("fw_freq_dist", CountVectorizer(analyzer="word",
                                             vocabulary=function_word_list,
                                             lowercase=True)),
            ("punct_freq_dist", CountVectorizer(tokenizer=punctuation_tokenizer,
                                                vocabulary=['.', '...', '?', '??', '???', '!', ';', ':', '\''],
                                                token_pattern=None)),
            #("sentence_length", SentenceLength()),
            #("avg_wl", AverageWordLength())
            ("caps", Capitalization())
        ],
        transformer_weights={
            "punct_freq_dist": 5.0,
            #"sentence_length": 5.0,
            #"avg_wl": 5.0
            "caps": 5.0
        }
        )),
        #("scaler", StandardScaler(with_mean=False)),
        ("clf", LinearSVC(class_weight="balanced"))
    ])
    return pipeline


def get_X_y(min_messages: int) -> tuple[list[str], list[str]]:
    author_messages = preprocess_remove_garbage(
        database.get_messages_with_x_plus_messages(min_messages, database.get_db_timestamp())
    )
    X, y = [], []
    for nick, msgs in author_messages.items():
        for msg in msgs:
            X.append(msg)
            y.append(nick)
    return X, y


def evaluate_pipeline(pipeline: Pipeline, X: list[str], y: list[str], cv: int = 5) -> tuple[np.ndarray, list[str], float]:
    y_pred_test = cross_val_predict(pipeline, X, y, cv=cv)
    cm = confusion_matrix(y, y_pred_test)
    acc = accuracy_score(y, y_pred_test)

    return cm, pipeline.classes_, acc


def plot_and_save_confusion_matrix(cm: np.ndarray, labels: list[str], filename: str = "cm.png"):
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap="Blues", xticks_rotation=45)
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(filename, dpi=300)