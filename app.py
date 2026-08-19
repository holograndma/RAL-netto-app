from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "docs"

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(PUBLIC, filename)


if __name__ == "__main__":
    app.run(debug=True)
