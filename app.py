import os
import math
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_URL = "https://v3.football.api-sports.io"


def poisson(lam, goals):
    return (math.exp(-lam) * lam ** goals) / math.factorial(goals)


def analyze_match(home, away):
    home_xg = 1.42
    away_xg = 1.12

    home_probs = [poisson(home_xg, i) for i in range(8)]
    away_probs = [poisson(away_xg, i) for i in range(8)]

    p_home = p_draw = p_away = 0
    p_over = p_btts = 0

    for h in range(8):
        for a in range(8):
            probability = home_probs[h] * away_probs[a]

            if h > a:
                p_home += probability
            elif h == a:
                p_draw += probability
            else:
                p_away += probability

            if h + a >= 3:
                p_over += probability

            if h > 0 and a > 0:
                p_btts += probability

    values = {
        "home": round(p_home * 100),
        "draw": round(p_draw * 100),
        "away": round(p_away * 100),
        "over25": round(p_over * 100),
        "under25": round((1 - p_over) * 100),
        "btts": round(p_btts * 100)
    }

    picks = {
        "1": values["home"],
        "X": values["draw"],
        "2": values["away"]
    }

    pick = max(picks, key=picks.get)

    return {
        "p": values,
        "pick": pick,
        "confidence": picks[pick]
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        today=datetime.now().strftime("%Y-%m-%d")
    )


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    if not API_KEY:
        return jsonify({
            "ok": False,
            "error": "API anahtarı sunucuya eklenmemiş."
        }), 500

    data = request.get_json(silent=True) or {}
    selected_date = data.get("date")

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({
            "ok": False,
            "error": "Geçerli bir tarih seç."
        }), 400

    try:
        response = requests.get(
            f"{API_URL}/fixtures",
            headers={"x-apisports-key": API_KEY},
            params={
                "date": selected_date,
                "timezone": "Europe/Istanbul"
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        if result.get("errors"):
            return jsonify({
                "ok": False,
                "error": "API hatası: " + str(result["errors"])
            }), 502

        matches = []

        for item in result.get("response", []):
            fixture = item["fixture"]
            teams = item["teams"]
            league = item["league"]

            analysis = analyze_match(
                teams["home"]["name"],
                teams["away"]["name"]
            )

            analysis.update({
                "home": teams["home"]["name"],
                "away": teams["away"]["name"],
                "league": league["name"],
                "country": league["country"],
                "time": fixture["date"][11:16]
            })

            matches.append(analysis)

        matches.sort(
            key=lambda match: match["confidence"],
            reverse=True
        )

        return jsonify({
            "ok": True,
            "count": len(matches),
            "matches": matches
        })

    except requests.RequestException:
        return jsonify({
            "ok": False,
            "error": "Maç verileri alınamadı. Daha sonra tekrar dene."
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
