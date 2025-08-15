from collections import defaultdict
from sklearn.feature_selection import SelectKBest, f_classif
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
from joblib import Memory

memory = Memory()

def preprocess_remove_garbage(author_message: dict[str, list[str]], quota: int = 400) -> defaultdict[str, list[str]]:
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

    cleaned_final = defaultdict(list)
    for author, messages in cleaned.items():
        if len(messages) < quota:
            continue
        cleaned_final[author] = messages


    return cleaned_final

"""
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
"""

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


class POSTagging(BaseEstimator, TransformerMixin):
    def __init__(self, model="en_core_web_sm"):
        self.model = model
        self.nlp = None

        self._posmap = [
            "",
            "ADJ",
            "ADP",
            "ADV",
            "AUX",
            "CONJ",
            "CCONJ",
            "DET",
            "INTJ",
            "NOUN",
            "NUM",
            "PART",
            "PRON",
            "PROPN",
            "PUNCT",
            "SCONJ",
            "SYM",
            "VERB",
            "X",
            "EOL",
            "SPACE"
        ]
        self.posmap = {i:e for e, i in enumerate(self._posmap)}

    def fit(self, X, y=None):
        import spacy

        # Strange pickle behaviour that prevents this to occur in __init__.
        self.nlp = spacy.load(self.model, disable=["ner", "parser", "lemmatizer"])

        return self

    def transform(self, X):
        author_pos = []

        for doc in self.nlp.pipe(X, batch_size=1000):
            posses = [0] * 21
            for token in doc:
                posses[self.posmap[token.pos_]] += 1
            author_pos.append(posses)

        return np.array(author_pos)
    

FUNCTION_WORDS = [
    'the', 'of', 'and', 'to', 'a', 'in', 'that', 'is', 'was', 'he', 'for', 'it',
    'with', 'as', 'his', 'on', 'be', 'at', 'by', 'i', 'this', 'had', 'not', 'are',
    'but', 'from', 'or', 'have', 'an', 'they', 'which', 'one', 'you', 'were',
    'her', 'all', 'she', 'there', 'would', 'their', 'we', 'him', 'been', 'has',
    'when', 'who', 'will', 'more', 'no', 'if', 'out', 'so', 'said', 'what', 'up',
    'its', 'about', 'into', 'than', 'them', 'can', 'only', 'other', 'new', 'some',
    'could', 'time', 'these', 'two', 'may', 'then', 'do', 'first', 'any', 'my',
    'now', 'such', 'like', 'our', 'over', 'man', 'me', 'even', 'most', 'made',
    'after', 'also', 'did', 'many', 'before', 'must', 'through', 'back', 'years',
    'where', 'much', 'your', 'way', 'well', 'down'
]
class FunctionWordVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.words = FUNCTION_WORDS
        self.word_to_idx = {w:e for e, w in enumerate(self.words)}

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        vectors = np.zeros((len(X), len(self.words)), dtype=float)
        for i, doc in enumerate(X):
            tokens = re.findall(r"\w+", doc.lower())
            total_tokens = len(tokens) if tokens else 1
            for token in tokens:
                if token in self.word_to_idx:
                    vectors[i, self.word_to_idx[token]] += 1
            vectors[i] /= total_tokens

        return vectors


def punctuation_tokenizer(text: str) -> list[str]:
    return re.findall(r'\.\.\.|[\?\!]{2,}|[.,;:!?\'"-]', text)

def create_pipeline(group_k: int = 1) -> Pipeline:
    if group_k > 1:
        reduced_tfidf = Pipeline([
            ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,4))),
            ("select_k_best", SelectKBest(score_func=f_classif, k=3000))
        ])
    else:
        reduced_tfidf = Pipeline([
            ("char_ngrams", TfidfVectorizer(analyzer="char", ngram_range=(2,4))),
        ])

    features = [
        ("reduced_tfidf", reduced_tfidf),
        ("punct_freq_dist", CountVectorizer(
            tokenizer=punctuation_tokenizer,
            vocabulary=['.', '...', '?', '???', '!', ';', ':', '\''],
            token_pattern=None
        )),
        ("caps", Capitalization()),
        ("pos", POSTagging())
    ]

    if group_k > 1:
        features.append(("func_words", FunctionWordVectorizer()))

    transformer_weights = {
        "caps": 1.15,
        "punct_freq_dist": 1.1,
        "reduced_tfidf": 1
    }

    pipeline = Pipeline([
        ("features", FeatureUnion(features, transformer_weights=transformer_weights)),
        ("clf", LinearSVC(class_weight="balanced"))
    ])

    return pipeline

def get_X_y(min_messages: int, cf: int = 0) -> tuple[list[str], list[str]]:
    author_messages = preprocess_remove_garbage(
        database.get_messages_with_x_plus_messages(min_messages, cf)
    , min_messages)

    X, y = [], []

    cap = int(min(len(v) for v in author_messages.values()) + min_messages*1.25)
    for nick, msgs in author_messages.items():
        shuffle(msgs)
        for msg in msgs[:cap]:
            X.append(msg)
            y.append(nick)

    return X, y

@memory.cache
def get_X_y_block(min_messages: int, cf: int = 0, group_k: int = 10, expire: int = 0) -> tuple[list[str], list[str]]:
    author_messages = preprocess_remove_garbage(
        database.get_messages_with_x_plus_messages(min_messages, cf)
    , min_messages)

    X, y = [], []
    cap = min_messages

    for nick, msgs in author_messages.items():
        shuffle(msgs)
        msgs = msgs[:cap]

        if group_k <= 1:
            for msg in msgs:
                X.append(msg)
                y.append(nick)
        else:
            for i in range(0, len(msgs), group_k):
                block_msgs = msgs[i:i+group_k]
                if len(block_msgs) == 0:
                    continue
                block = "   ".join(block_msgs).strip()
                if block:
                    X.append(block)
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
    pipeline = create_pipeline(5)
    X, y = get_X_y_block(400, 5, 5)
    pipeline.fit(X, y)
    #X, y = get_X_y2(400, 14)
    print(pipeline.named_steps["clf"].classes_)

    c = cross_validate(pipeline, X, y, cv=5, scoring=["accuracy", "f1_macro"])
    print(f"accuracy:\t{c['test_accuracy'].mean()}\nf1:\t{c['test_f1_macro'].mean()}")
