import os
import math
import time
import requests
from datetime import date, timedelta
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_URL = "https://v3.football.api-sports.io"

CACHE = {}
CACHE_TIME = 900


def api_get(endpoint, params=None):
    if not API_KEY:
        raise Exception("API_FOOTBALL_KEY ayarlanmamış.")

    params = params or {}
    key = (endpoint, tuple(sorted(params.items())))
    now = time.time()

    if key in CACHE:
        saved_time, saved_data = CACHE[key]
        if now - saved_time < CACHE_TIME:
            return saved_data

    response = requests.get(
        API_URL + endpoint,
        headers={"x-apisports-key": API_KEY},
        params=params,
        timeout=25
    )

    if response.status_code == 401:
        raise Exception("API anahtarı geçersiz.")
    if response.status_code == 403:
        raise Exception("API erişimi reddedildi.")
    if response.status_code == 429:
        raise Exception("Günlük API istek limitine ulaşıldı.")

    response.raise_for_status()
    data = response.json()

    if data.get("errors"):
        raise Exception(str(data["errors"]))

    CACHE[key] = (now, data)
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/fixtures")
def fixtures():
    selected_date = request.args.get("date")

    if not selected_date:
        return jsonify({"error": "Tarih belirtilmedi."}), 400

    try:
        data = api_get("/fixtures", {"date": selected_date})

        matches = []

        for item in data.get("response", []):
            fixture = item["fixture"]
            teams = item["teams"]
            league = item["league"]

            matches.append({
                "id": fixture["id"],
                "date": fixture["date"],
                "time": fixture["date"][11:16],
                "status": fixture["status"]["short"],
                "home_team": teams["home"]["name"],
                "away_team": teams["away"]["name"],
                "home_team_id": teams["home"]["id"],
                "away_team_id": teams["away"]["id"],
                "home_logo": teams["home"]["logo"],
                "away_logo": teams["away"]["logo"],
                "league": league["name"],
                "country": league["country"]
            })

        return jsonify({"fixtures": matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_team_stats(team_id):
    today = date.today()
    start = today - timedelta(days=120)

    params = {
        "team": team_id,
        "from": start.isoformat(),
        "to": today.isoformat(),
        "season": today.year,
        "status": "FT",
        "timezone": "Europe/Istanbul"
    }

    data = api_get("/fixtures", params)
    matches = data.get("response", [])

    # Diğer sayfaları da al
    paging = data.get("paging", {})
    total_pages = int(paging.get("total", 1))

    for page in range(2, total_pages + 1):
        page_params = dict(params)
        page_params["page"] = page

        extra = api_get("/fixtures", page_params)
        matches.extend(extra.get("response", []))

    # Tekrarlanan maçları temizle
    unique_matches = {}

    for match in matches:
        unique_matches[match["fixture"]["id"]] = match

    matches = list(unique_matches.values())

    # En yeni 10 tamamlanmış maçı seç
    matches.sort(
        key=lambda m: m["fixture"]["date"],
        reverse=True
    )

    matches = matches[:10]

    scored = []
    conceded = []
    wins = 0
    draws = 0
    losses = 0

    for match in matches:
        goals = match.get("goals", {})
        teams = match.get("teams", {})

        home_id = teams["home"]["id"]
        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        if team_id == home_id:
            scored.append(home_goals)
            conceded.append(away_goals)

            if home_goals > away_goals:
                wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                losses += 1
        else:
            scored.append(away_goals)
            conceded.append(home_goals)

            if away_goals > home_goals:
                wins += 1
            elif away_goals == home_goals:
                draws += 1
            else:
                losses += 1

    if not scored:
        raise Exception("Takımın son maç verileri bulunamadı.")

    return {
        "played": len(scored),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "scored": round(sum(scored) / len(scored), 2),
        "conceded": round(sum(conceded) / len(conceded), 2)
    }


def poisson_probability(lam, goals):
    return (math.exp(-lam) * lam ** goals) / math.factorial(goals)


def calculate_probabilities(home_xg, away_xg):
    home_win = 0
    draw = 0
    away_win = 0
    over_25 = 0
    btts = 0

    for h in range(9):
        for a in range(9):
            probability = (
                poisson_probability(home_xg, h) *
                poisson_probability(away_xg, a)
            )

            if h > a:
                home_win += probability
            elif h == a:
                draw += probability
            else:
                away_win += probability

            if h + a >= 3:
                over_25 += probability

            if h > 0 and a > 0:
                btts += probability

    return {
        "home_win": round(home_win * 100, 1),
        "draw": round(draw * 100, 1),
        "away_win": round(away_win * 100, 1),
        "over_25": round(over_25 * 100, 1),
        "under_25": round((1 - over_25) * 100, 1),
        "btts_yes": round(btts * 100, 1),
        "btts_no": round((1 - btts) * 100, 1)
    }


@app.route("/api/analyze", methods=["GET", "POST"])
def analyze():
    try:
        if request.method == "POST":
            body = request.get_json(silent=True) or {}
        else:
            body = request.args

        home_id = int(
            body.get("home_id") or body.get("home_team_id")
        )

        away_id = int(
            body.get("away_id") or body.get("away_team_id")
        )

        home = get_team_stats(home_id)
        away = get_team_stats(away_id)

        home_xg = (
            home["scored"] * 0.60 +
            away["conceded"] * 0.40
        )

        away_xg = (
            away["scored"] * 0.60 +
            home["conceded"] * 0.40
        )

        home_xg = max(0.15, min(home_xg, 4.5))
        away_xg = max(0.15, min(away_xg, 4.5))

        probabilities = calculate_probabilities(
            home_xg,
            away_xg
        )

        return jsonify({
            "home": home,
            "away": away,
            "home_stats": home,
            "away_stats": away,
            "home_xg": round(home_xg, 2),
            "away_xg": round(away_xg, 2),
            "xg": {
                "home": round(home_xg, 2),
                "away": round(away_xg, 2)
            },
            "probabilities": probabilities,
            "note": (
                "Tahminler takımların son 10 tamamlanmış "
                "maçındaki gol istatistiklerine dayanır. "
                "Kesin sonuç garantisi değildir."
            )
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
            
