const btn = document.getElementById('analyze');
const msg = document.getElementById('message');
const results = document.getElementById('results');

btn.addEventListener('click', async () => {
    const day = document.getElementById('date').value;
    if (!day) {
        msg.textContent = 'Lütfen tarih seç.';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Analiz ediliyor...';
    msg.textContent = 'Maçlar taranıyor...';
    results.innerHTML = '';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({date: day})
        });

        const data = await response.json();
        if (!response.ok || !data.ok) {
            throw new Error(data.error || 'Analiz başarısız.');
        }

        msg.textContent = `${data.count} maç bulundu.`;

        data.matches.forEach(m => {
            const el = document.createElement('article');
            el.className = 'match';
            el.innerHTML = `
                <div class="meta">${m.league} · ${m.country} · ${m.time}</div>
                <h3>${m.home} – ${m.away}</h3>
                <div class="pick">En yüksek 1X2: ${m.pick} · %${m.confidence}</div>
                <div class="stats">
                    <div class="stat">1<b>%${m.p.home}</b></div>
                    <div class="stat">X<b>%${m.p.draw}</b></div>
                    <div class="stat">2<b>%${m.p.away}</b></div>
                    <div class="stat">2,5 Üst<b>%${m.p.over25}</b></div>
                    <div class="stat">2,5 Alt<b>%${m.p.under25}</b></div>
                    <div class="stat">KG Var<b>%${m.p.btts}</b></div>
                </div>`;
            results.appendChild(el);
        });
    } catch (error) {
        msg.textContent = 'Hata: ' + error.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '🔎 ANALİZ ET';
    }
});
