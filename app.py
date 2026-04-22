from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

USERS_FILE = "users.json"
RESULTS_FILE = "results.json"

# ---------- Helpers ----------
def read_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def write_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Auth ----------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    users = read_json(USERS_FILE)

    if any(u["email"] == data["email"] for u in users):
        return jsonify({"msg": "User exists"}), 400

    users.append({
        "name": data.get("name", ""),
        "email": data["email"],
        "password": data["password"],
        "created_at": datetime.now().isoformat()
    })
    write_json(USERS_FILE, users)
    return jsonify({"msg": "Signup successful"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    users = read_json(USERS_FILE)

    user = next(
        (u for u in users if u["email"] == data["email"] and u["password"] == data["password"]),
        None
    )

    if not user:
        return jsonify({"msg": "Invalid credentials"}), 401

    return jsonify({"msg": "Login success", "user": data["email"], "name": user.get("name", "")})


# ---------- Submit Test ----------
@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    results = read_json(RESULTS_FILE)

    weak_topics = []
    subject = data.get("subject", "")
    topic_scores = data.get("answers", {}).get(subject, {})

    for topic, score in topic_scores.items():
        total = data.get("topic_totals", {}).get(topic, 5)
        pct = score / total if total else 0
        if pct < 0.6:
            weak_topics.append({
                "subject": subject,
                "topic": topic,
                "score": score,
                "total": total
            })

    record = {
        "user": data["user"],
        "subject": subject,
        "score": data.get("score", 0),
        "weak_topics": weak_topics,
        "topic_scores": topic_scores,
        "timestamp": datetime.now().isoformat()
    }

    results.append(record)
    write_json(RESULTS_FILE, results)

    return jsonify(record)


# ---------- Get Results ----------
@app.route("/results/<user>", methods=["GET"])
def get_results(user):
    results = read_json(RESULTS_FILE)
    user_data = [r for r in results if r["user"] == user]
    return jsonify(user_data)


# ---------- Health ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
