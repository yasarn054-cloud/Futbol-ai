const dateInput = document.getElementById("matchDate");
const loadButton = document.getElementById("loadMatches");
const searchInput = document.getElementById("searchInput");
const matchesContainer = document.getElementById("matches");
const matchCount = document.getElementById("matchCount");
const analysisResult = document.getElementById("analysisResult");

let allMatches = [];

dateInput.value = new Date().toLocaleDateString("en-CA");

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);
}

async function loadMatches() {
    const date = dateInput.value;

    if (!date) {
        alert("Lütfen tarih seç.");
        return;
    }

    loadButton.disabled = true;
    loadButton.textContent = "Yükleniyor...";
    matchesContainer.innerHTML = '<div class="empty">Maç verileri alınıyor...</div>';

    try {
        const response = await fetch(`/api/fixtures?date=${encodeURIComponent(date)}`);
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Maçlar alınamadı.");
        }

        allMatches = data.fixtures || [];
        renderMatches();

    } catch (error) {
        matchesContainer.innerHTML =
            `<div class="empty">${escapeHTML(error.message)}</div>`;
        matchCount.textContent = "Maçlar yüklenemedi.";
    } finally {
        loadButton.disabled = false;
        loadButton.textContent = "Maçları getir";
    }
}

function renderMatches() {
    const query = searchInput.value.trim().toLocaleLowerCase("tr-TR");

    const filtered = allMatches.filter(match => {
        const searchable = [
            match.home_team,
            match.away_team,
            match.league,
            match.country
        ].join(" ").toLocaleLowerCase("tr-TR");

        return searchable.includes(query);
    });

    matchCount.textContent =
        `${filtered.length} maç gösteriliyor · Toplam ${allMatches.length} maç`;

    if (!filtered.length) {
        matchesContainer.innerHTML =
            '<div class="empty">Aramana uygun maç bulunamadı.</div>';
        return;
    }

    matchesContainer.innerHTML = filtered.map(match => `
        <article class="match-card">
            <div class="match-league">
                ${escapeHTML(match.country)} · ${escapeHTML(match.league)}
            </div>
            <div class="teams">
                <div class="team">${escapeHTML(match.home_team)}</div>
                <div class="vs">VS</div>
                <div class="team">${escapeHTML(match.away_team)}</div>
            </div>
            <div class="match-time">
                ${escapeHTML(match.time)} · ${escapeHTML(match.status)}
            </div>
            <button class="analyze-button"
                data-home="${Number(match.home_team_id)}"
                data-away="${Number(match.away_team_id)}">
                Maçı analiz et
            </button>
        </article>
    `).join("");

    matchesContainer.querySelectorAll(".analyze-button").forEach(button => {
        button.addEventListener("click", () => {
            analyzeMatch(button.dataset.home, button.dataset.away, button);
        });
    });
}

async function analyzeMatch(homeId, awayId, button) {
    button.disabled = true;
    button.textContent = "Analiz ediliyor...";

    analysisResult.innerHTML =
        '<div class="empty">Takımların son 10 maçı inceleniyor...</div>';

    document.getElementById("analysisPanel").scrollIntoView({
        behavior: "smooth"
    });

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                home_id: Number(homeId),
                away_id: Number(awayId)
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Analiz yapılamadı.");
        }

        showAnalysis(data);

    } catch (error) {
        analysisResult.innerHTML =
            `<div class="empty">${escapeHTML(error.message)}</div>`;
    } finally {
        button.disabled = false;
        button.textContent = "Maçı analiz et";
    }
}

function showAnalysis(data) {
    const home = data.home || data.home_stats;
    const away = data.away || data.away_stats;
    const p = data.probabilities || {};

    const statCard = (label, value) => `
        <div class="stat-card">
            <small>${label}</small>
            <strong>${escapeHTML(value)}</strong>
        </div>
    `;

    const probCard = (label, value) => `
        <div class="prob-card">
            <small>${label}</small>
            <strong>%${escapeHTML(value ?? "-")}</strong>
        </div>
    `;

    analysisResult.innerHTML = `
        <div class="team-analysis">
            <h4>Ev sahibi takım</h4>
            <div class="stats-grid">
                ${statCard("Galibiyet", home.wins)}
                ${statCard("Beraberlik", home.draws)}
                ${statCard("Mağlubiyet", home.losses)}
                ${statCard("Maç başı gol", home.scored)}
                ${statCard("Maç başı yenilen gol", home.conceded)}
                ${statCard("Oynanan maç", home.played)}
            </div>
        </div>

        <div class="team-analysis">
            <h4>Deplasman takımı</h4>
            <div class="stats-grid">
                ${statCard("Galibiyet", away.wins)}
                ${statCard("Beraberlik", away.draws)}
                ${statCard("Mağlubiyet", away.losses)}
                ${statCard("Maç başı gol", away.scored)}
                ${statCard("Maç başı yenilen gol", away.conceded)}
                ${statCard("Oynanan maç", away.played)}
            </div>
        </div>

        <div class="team-analysis">
            <h4>🎯 Tahmini gol beklentisi</h4>
            <div class="stats-grid">
                ${statCard("Ev sahibi xG", data.home_xg)}
                ${statCard("Deplasman xG", data.away_xg)}
            </div>
        </div>

        <div class="team-analysis">
            <h4>📈 Olasılık tahminleri</h4>
            <div class="prob-grid">
                ${probCard("Ev sahibi kazanır", p.home_win)}
                ${probCard("Beraberlik", p.draw)}
                ${probCard("Deplasman kazanır", p.away_win)}
                ${probCard("2.5 üst", p.over_25)}
                ${probCard("2.5 alt", p.under_25)}
                ${probCard("Karşılıklı gol var", p.btts_yes)}
                ${probCard("Karşılıklı gol yok", p.btts_no)}
            </div>
        </div>

        <div class="note">
            ${escapeHTML(data.note || "Tahminler istatistiksel değerlendirmedir; kesin sonuç garantisi değildir.")}
        </div>
    `;
}

loadButton.addEventListener("click", loadMatches);
searchInput.addEventListener("input", renderMatches);

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
}
