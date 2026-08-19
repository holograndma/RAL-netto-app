from __future__ import annotations

from flask import Flask, render_template, request

from italy_net_income import calculate_net, comparison_curve, display_rows, parse_ral

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    ral_input = request.values.get("ral", "").strip()
    error = None
    rows = None
    result = None
    curve = None

    if ral_input:
        try:
            ral = parse_ral(ral_input)
            result = calculate_net(ral)
            rows = display_rows(result)
            curve = comparison_curve(ral)
        except ValueError as exc:
            error = str(exc)

    return render_template(
        "index.html",
        ral_input=ral_input,
        error=error,
        rows=rows,
        result=result,
        curve=curve,
    )


if __name__ == "__main__":
    app.run(debug=True)
