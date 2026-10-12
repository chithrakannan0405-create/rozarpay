
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)

# 1. Generate synthetic transaction data
rng = np.random.default_rng(42)
n = 2000

df = pd.DataFrame({
    "amount": rng.lognormal(7, 1, n).clip(50, 100000),
    "failed_attempts": rng.poisson(1.2, n).clip(0, 10),
    "transactions_last_10m": rng.poisson(2, n).clip(0, 15),
    "account_age_days": rng.integers(1, 1000, n),
})

# 2. Create simulated labels for learning purposes
df["is_fraud"] = (
    (
        (df["failed_attempts"] >= 5)
        & (df["transactions_last_10m"] >= 6)
    )
    | (
        (df["account_age_days"] < 7)
        & (df["amount"] >= 25000)
        & (df["failed_attempts"] >= 2)
    )
).astype(int)

features = [
    "amount",
    "failed_attempts",
    "transactions_last_10m",
    "account_age_days",
]

X = df[features]
y = df["is_fraud"]

# 3. Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

# 4. Create the model BEFORE calling model.fit()
model = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
    ),
)

# 5. Train the model
model.fit(X_train, y_train)

# 6. Evaluate the model on unseen test rows
predictions = model.predict(X_test)

print("\n=== FraudSpike AI: Model Evaluation ===")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Accuracy:", round(accuracy_score(y_test, predictions), 3))
print(
    "Precision:",
    round(precision_score(y_test, predictions, zero_division=0), 3),
)
print(
    "Recall:",
    round(recall_score(y_test, predictions, zero_division=0), 3),
)
print("\nConfusion matrix:")
print(confusion_matrix(y_test, predictions))
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

# 7. Save the trained model for the dashboard
model_path = Path(__file__).resolve().parent / "fraud_model.joblib"

joblib.dump(
    {
        "model": model,
        "features": features,
    },
    model_path,
)

print("\nModel saved successfully!")
print("Location:", model_path)
