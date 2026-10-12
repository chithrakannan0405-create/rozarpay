
import pandas as pd
import streamlit as st

from pathlib import Path
from risk_engine import assess_risk


# -----------------------------
# 1. Page configuration
# -----------------------------
st.set_page_config(
    page_title="FraudSpike AI",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ FraudSpike AI")
st.caption(
    "Payment risk monitoring and explainable risk assessment"
)

st.info(
    "Demo mode: all transactions are synthetic. "
    "Risk scores come from illustrative rules, not a "
    "validated fraud prediction model."
)


# -----------------------------
# 2. Load sample transaction data
# -----------------------------
DATA_PATHS = [
    Path(__file__).parent / "data" / "transactions.csv",
    Path(__file__).parent / "transaction.csv",
]


def resolve_data_path():
    for path in DATA_PATHS:
        if path.exists():
            return path
    return DATA_PATHS[0]


DATA_PATH = resolve_data_path()


@st.cache_data
def load_transactions(path):
    df = pd.read_csv(path)

    required_columns = [
        "transaction_id",
        "amount",
        "failed_attempts",
        "transactions_last_10m",
        "account_age_days",
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing CSV columns: {', '.join(sorted(missing))}"
        )

    if df.empty:
        raise ValueError("The transaction CSV is empty.")

    numeric_columns = [
        "amount",
        "failed_attempts",
        "transactions_last_10m",
        "account_age_days",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    if df[numeric_columns].isna().any().any():
        raise ValueError(
            "Transaction data contains missing values."
        )

    if (df[numeric_columns] < 0).any().any():
        raise ValueError(
            "Transaction values cannot be negative."
        )

    return df


try:
    df = load_transactions(str(DATA_PATH))
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Could not load transaction data: {error}")
    st.stop()


# -----------------------------
# 3. Assess every sample transaction
# -----------------------------
results = []

for _, transaction in df.iterrows():
    result = assess_risk(
        amount=float(transaction["amount"]),
        failed_attempts=int(
            transaction["failed_attempts"]
        ),
        transactions_last_10m=int(
            transaction["transactions_last_10m"]
        ),
        account_age_days=int(
            transaction["account_age_days"]
        ),
    )

    results.append(result)

df["risk_score"] = [
    result["risk_score"] for result in results
]

df["risk_category"] = [
    result["risk_category"] for result in results
]

df["risk_reasons"] = [
    "; ".join(result["reasons"])
    for result in results
]


# -----------------------------
# 4. Dashboard metrics
# -----------------------------
high_risk = int(
    (df["risk_category"] == "High").sum()
)

medium_risk = int(
    (df["risk_category"] == "Medium").sum()
)

low_risk = int(
    (df["risk_category"] == "Low").sum()
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Transactions",
    len(df),
)

col2.metric(
    "High risk",
    high_risk,
)

col3.metric(
    "Medium risk",
    medium_risk,
)

col4.metric(
    "Low risk",
    low_risk,
)


# -----------------------------
# 5. Risk distribution chart
# -----------------------------
st.subheader("Risk distribution")

distribution = pd.DataFrame({
    "Risk level": ["Low", "Medium", "High"],
    "Transactions": [low_risk, medium_risk, high_risk],
})

st.bar_chart(
    distribution.set_index("Risk level")
)


# -----------------------------
# 6. Transaction monitor
# -----------------------------
st.subheader("Transaction monitor")

selected_risk = st.selectbox(
    "Filter by risk category",
    ["All", "Low", "Medium", "High"],
)

if selected_risk == "All":
    filtered_df = df.copy()
else:
    filtered_df = df[
        df["risk_category"] == selected_risk
    ]

st.dataframe(
    filtered_df[
        [
            "transaction_id",
            "amount",
            "failed_attempts",
            "transactions_last_10m",
            "risk_score",
            "risk_category",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


# -----------------------------
# 7. Investigate a transaction
# -----------------------------
st.subheader("Investigate a transaction")

transaction_ids = df["transaction_id"].astype(str).tolist()

selected_id = st.selectbox(
    "Choose a sample transaction",
    transaction_ids,
)

transaction = df[
    df["transaction_id"].astype(str) == selected_id
].iloc[0]

assessment = assess_risk(
    amount=float(transaction["amount"]),
    failed_attempts=int(transaction["failed_attempts"]),
    transactions_last_10m=int(
        transaction["transactions_last_10m"]
    ),
    account_age_days=int(transaction["account_age_days"]),
)

left, right = st.columns(2)

with left:
    st.metric(
        "Risk score",
        f'{assessment["risk_score"]} / 100',
    )

    st.metric(
        "Risk category",
        assessment["risk_category"],
    )

with right:
    st.write("**Transaction details**")
    st.write(f'Amount: ₹{transaction["amount"]:,.2f}')
    st.write(
        f'Failed attempts: {transaction["failed_attempts"]}'
    )
    st.write(
        "Transactions in last 10 minutes: "
        f'{transaction["transactions_last_10m"]}'
    )
    st.write(
        f'Account age: {transaction["account_age_days"]} days'
    )

st.write("**Why was this transaction flagged?**")

for reason in assessment["reasons"]:
    st.write(f"- {reason}")

st.write("**Suggested next step**")
st.write(assessment["recommended_action"])

st.caption(
    "A risk flag is not proof of fraud. "
    "Use appropriate human review before taking action."
)


# -----------------------------
# 8. Test a custom transaction
# -----------------------------
st.subheader("Test a new transaction")

with st.form("risk_assessment_form"):
    amount = st.number_input(
        "Payment amount (₹)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
    )

    failures = st.number_input(
        "Failed attempts",
        min_value=0,
        value=0,
        step=1,
    )

    frequency = st.number_input(
        "Transactions in the last 10 minutes",
        min_value=0,
        value=1,
        step=1,
    )

    account_age = st.number_input(
        "Account age (days)",
        min_value=0,
        value=90,
        step=1,
    )

    submitted = st.form_submit_button(
        "Analyze transaction",
        type="primary",
    )

if submitted:
    custom_result = assess_risk(
        amount=amount,
        failed_attempts=failures,
        transactions_last_10m=frequency,
        account_age_days=account_age,
    )

    st.divider()
    st.subheader("Assessment result")

    st.metric(
        "Risk score",
        f'{custom_result["risk_score"]} / 100',
    )

    st.write(
        f'**Risk level:** {custom_result["risk_category"]}'
    )

    st.write("**Triggered rules**")

    for reason in custom_result["reasons"]:
        st.write(f"- {reason}")

    st.write(
        "**Suggested action:** "
        f'{custom_result["recommended_action"]}'
    )

    st.caption(
        "This is a demonstration assessment, not a "
        "validated prediction of fraud."
    )


# -----------------------------
# 9. Footer
# -----------------------------
st.divider()

st.caption(
    "FraudSpike AI | Buildathon prototype | Synthetic data only"
)
