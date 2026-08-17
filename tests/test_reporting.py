import pandas as pd

from next_best_action.reporting import spreadsheet_safe


def test_spreadsheet_safe_neutralizes_formula_prefixed_text_only():
    frame = pd.DataFrame(
        {
            "customer_id": ["=1+1", "+SUM(A1:A2)", "-cmd", "@risk", "SAFE-1"],
            "value": [-1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    safe = spreadsheet_safe(frame)

    assert safe["customer_id"].tolist() == [
        "'=1+1",
        "'+SUM(A1:A2)",
        "'-cmd",
        "'@risk",
        "SAFE-1",
    ]
    assert safe["value"].tolist() == frame["value"].tolist()
