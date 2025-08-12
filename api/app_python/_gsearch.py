from sklearn.model_selection import GridSearchCV
from s_retrain import create_pipeline, get_X_y

pipeline = create_pipeline()

param_grid = {
    "features__transformer_weights": [
        {"caps": 1.5, "punct_freq_dist": 1.3, "reduced_tfidf": 0.7, "wl_dist": 1.0},
    ]
}

grid = GridSearchCV(
    pipeline,
    param_grid,
    scoring="f1_macro",
    cv=10,
    n_jobs=-1
)

X, y = get_X_y(400)

grid.fit(X, y)

print("Best params:", grid.best_params_)
print("Best score:", grid.best_score_)
