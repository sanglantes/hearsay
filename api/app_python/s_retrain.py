from collections import defaultdict
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.base import BaseEstimator, TransformerMixin
import database
import numpy as np
import re
import matplotlib.pyplot as plt
from random import shuffle

def preprocess_remove_garbage(author_message: dict[str, list[str]]) -> defaultdict[str, list[str]]:
    cleaned = defaultdict(list)

    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    quote_pattern = re.compile(r'^[><."“!:*\[]')
    for author, messages in author_message.items():
        for message in messages:
            if (
                url_pattern.search(message) or
                quote_pattern.match(message)
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
    

def punctuation_tokenizer(text: str) -> list[str]:
    return re.findall(r'\.\.\.|[\?\!]{2,}|[.,;:!?\'"-]', text)

def create_pipeline() -> Pipeline:
    pipeline = Pipeline([
        ("features", FeatureUnion([
            ("reduced_tfidf", Pipeline([
                ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,4), lowercase=True)),
                #("sb", SelectKBest(score_func=f_classif, k=1000))
            ])),
            ("punct_freq_dist", CountVectorizer(tokenizer=punctuation_tokenizer,
                                                vocabulary=['.', '...', '?', '???', '!', ';', ':', '\''],
                                                token_pattern=None)),
            ("wl_dist", WordLengthDistribution()),
            ("caps", Capitalization()),
        ],
        transformer_weights={
            "caps": 1.5,
            "punct_freq_dist": 1.1
        }
        )),
        ("clf", LinearSVC())
    ])

    return pipeline

def get_X_y(min_messages: int) -> tuple[list[str], list[str]]:
    author_messages = preprocess_remove_garbage(
        database.get_messages_with_x_plus_messages(min_messages, database.get_db_timestamp())
    )
    X, y = [], []
    cap = min(len(v) for v in author_messages.values()) + 400
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
    X, y = get_X_y(400)
    pipeline.fit(X, y)
    print(pipeline.named_steps["clf"].classes_)

    c = cross_validate(pipeline, X, y, cv=10, scoring=["accuracy", "f1_macro"])
    print(f"accuracy:\t{c['test_accuracy'].mean()}\nf1:\t{c['test_f1_macro'].mean()}")
