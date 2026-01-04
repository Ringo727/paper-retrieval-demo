async function apiGet(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

async function apiPost(path, body = null) {
    const opts = { method: "POST" };
    if (body) opts.body = body;
    const res = await fetch(path, opts);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

function setStatus(msg) {
    document.getElementById("status").textContent = msg;
}

function renderResults(data) {
    const container = document.getElementById("results");
    container.innerHTML = "";

    const results = data.results || [];
    if (results.length === 0) {
        container.innerHTML = `<p class="muted">No results.</p>`;
        return;
    }

    for (const r of results) {
        const el = document.createElement("div");
        el.className = "card";
        el.innerHTML = `
      <div><strong>${escapeHtml(r.filename)}</strong></div>
      <div class="muted mono">score: ${Number(r.score).toFixed(4)} | doc_id: ${escapeHtml(r.doc_id)}</div>
      <pre>${escapeHtml(r.snippet || "")}</pre>
    `;
        container.appendChild(el);
    }
}

function escapeHtml(s) {
    return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function refreshStats() {
    const s = await apiGet("/stats");
    setStatus(`docs=${s.num_docs}, indexed=${s.indexed}`);
}

document.getElementById("loadDemoBtn").addEventListener("click", async () => {
    try {
        setStatus("Loading demo PDFs...");
        const maxPages = document.getElementById("maxPages").value || "10";
        await apiPost(`/load_demo?max_pages=${encodeURIComponent(maxPages)}`);
        await refreshStats();
    } catch (e) {
        setStatus(`Error: ${e.message}`);
    }
});

document.getElementById("resetBtn").addEventListener("click", async () => {
    try {
        setStatus("Resetting...");
        await apiPost("/reset");
        document.getElementById("results").innerHTML = "";
        document.getElementById("uploadLog").textContent = "";
        await refreshStats();
    } catch (e) {
        setStatus(`Error: ${e.message}`);
    }
});

document.getElementById("uploadBtn").addEventListener("click", async () => {
    const input = document.getElementById("pdfInput");
    const files = input.files;
    const log = document.getElementById("uploadLog");
    log.textContent = "";

    if (!files || files.length === 0) {
        log.textContent = "Choose at least one PDF.";
        return;
    }

    const maxPages = document.getElementById("maxPages").value || "10";

    try {
        setStatus(`Uploading ${files.length} file(s)...`);

        for (const f of files) {
            const form = new FormData();
            form.append("file", f);

            const resp = await apiPost(`/upload?max_pages=${encodeURIComponent(maxPages)}`, form);
            log.textContent += `Uploaded: ${resp.filename} (chars=${resp.text_chars ?? "?"})\n`;
        }

        await refreshStats();
        setStatus("Upload complete.");
        input.value = "";
    } catch (e) {
        setStatus(`Error: ${e.message}`);
    }
});

document.getElementById("searchBtn").addEventListener("click", async () => {
    const q = document.getElementById("query").value.trim();
    const k = document.getElementById("k").value || "10";

    if (!q) {
        setStatus("Enter a query.");
        return;
    }

    try {
        setStatus("Searching...");
        const data = await apiGet(`/search?q=${encodeURIComponent(q)}&k=${encodeURIComponent(k)}`);
        renderResults(data);
        await refreshStats();
        setStatus("Done.");
    } catch (e) {
        setStatus(`Error: ${e.message}`);
    }
});

// initial
refreshStats().catch(() => { });
