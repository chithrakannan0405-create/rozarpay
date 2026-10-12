
def assess_risk(
    amount,
    failed_attempts,
    transactions_last_10m,
    account_age_days,
):
    """
    Return an illustrative risk score, category, and reasons.

    This is a demonstration rules engine, not a validated
    fraud prediction model.
    """

    score = 0
    reasons = []

    # Rule 1: repeated failed payment attempts
    if failed_attempts >= 5:
        score += 35
        reasons.append(
            "Five or more failed payment attempts"
        )
    elif failed_attempts >= 3:
        score += 20
        reasons.append(
            "Several failed payment attempts"
        )

    # Rule 2: unusually frequent transactions
    if transactions_last_10m >= 8:
        score += 35
        reasons.append(
            "High transaction frequency in 10 minutes"
        )
    elif transactions_last_10m >= 5:
        score += 15
        reasons.append(
            "Elevated transaction frequency"
        )

    # Rule 3: new account combined with a large payment
    if account_age_days < 7 and amount >= 25000:
        score += 25
        reasons.append(
            "New account with a high-value payment"
        )

    # Rule 4: high amount alone contributes only a little
    if amount >= 50000:
        score += 10
        reasons.append(
            "Payment amount exceeds the demo threshold"
        )

    # Keep score within 0–100
    score = min(score, 100)

    # Assign a risk category
    if score >= 60:
        category = "High"
    elif score >= 30:
        category = "Medium"
    else:
        category = "Low"

    if not reasons:
        reasons.append(
            "No configured risk rules were triggered"
        )

    return {
        "risk_score": score,
        "risk_category": category,
        "reasons": reasons,
        "recommended_action": (
            "Flag for manual review"
            if category == "High"
            else "Review if additional concerns exist"
            if category == "Medium"
            else "Continue routine monitoring"
        ),
    }
