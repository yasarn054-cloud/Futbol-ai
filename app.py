import os, math, requests
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
API_HOST = "https://v3.football.api-sports.io"

def api_get(path, params):
    if not API_KEY:
        raise RuntimeError("API_FOOTBALL_KEY ayarlanmamış. Sunucu ortam değişkenlerine API-Football anahtarını ekleyin.")
    r = requests.get(API_HOST + path, headers={"x-apisports-key": API_KEY},
                     params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data.get("response", [])

def poisson(lam, k):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def estimate(home, away):
    # İlk sürüm: API'nin maç listesinde sağladığı lig/ev-deplasman bilgisiyle
    # genel başlangıç oranları. Sonuçlar kesin tahmin değildir.
    home_xg, away_xg = 1.42, 1.12
    h, d, a = 0.0, 0.0, 0.0
    over, btts = 0.0, 0.0
    for i in range(7):
        for j in range(7):
            p = poisson(home_xg, i) * poisson(away_xg, j)
            if i > j: h += p
            elif i == j: d += p
            else: a += p
            if i + j >= 3: over += p
            if i > 0 and j > 0: btts += p
    return {"home": round(h*100,1), "draw": round(d*100,1),
            "away": round(a*100,1), "over25": round(over*100,1),
            "under25": round((1-over)*100,1), "btts": round(btts*100,1)}

@app.get("/")
def index():
    today = date.today().isoformat()
    return render_template("index.html", today=today)

@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    day = payload.get("date", date.today().isoformat())
    try:
        datetime.strptime(day, "%Y-%m-%d")
        fixtures = api_get("/fixtures", {"date": day})
        matches = []
        for item in fixtures:
            f = item.get("fixture", {})
            teams = item.get("teams", {})
            league = item.get("league", {})
            probs = estimate(teams.get("home",{}).get("name",""), teams.get("away",{}).get("name",""))
            top = max([("1",probs["home"]),("X",probs["draw"]),("2",probs["away"])], key=lambda x:x[1])
            matches.append({
                "time": (f.get("date","")[11:16] or "--:--"),
                "league": league.get("name","Bilinmeyen Lig"),
                "country": league.get("country",""),
                "home": teams.get("home",{}).get("name","Ev sahibi"),
                "away": teams.get("away",{}).get("name","Deplasman"),
                "status": f.get("status",{}).get("short",""),
                "pick": top[0], "confidence": top[1], "p": probs
            })
        matches.sort(key=lambda m: m["confidence"], reverse=True)
        return jsonify({"ok": True, "date": day, "count": len(matches), "matches": matches,
                        "note": "Bu ilk sürüm genel Poisson başlangıç modeli kullanır; takım formu, kadro ve sakatlık verileri henüz modele dahil değildir."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
