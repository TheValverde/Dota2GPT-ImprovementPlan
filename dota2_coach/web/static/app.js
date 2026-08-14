const form = document.getElementById("analyze-form");
const playerInput = document.getElementById("player");
const matchInput = document.getElementById("match-id");
const playerResults = document.getElementById("player-results");
const recent = document.getElementById("recent");
const recentList = document.getElementById("recent-list");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit");
const output = document.getElementById("output");

let searchTimer = null;
let selectedAccountId = null;

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return payload;
}

playerInput.addEventListener("input", () => {
  selectedAccountId = null;
  const query = playerInput.value.trim();
  window.clearTimeout(searchTimer);
  if (query.length < 2 || /^\d+$/.test(query)) {
    playerResults.hidden = true;
    playerResults.innerHTML = "";
    return;
  }
  searchTimer = window.setTimeout(async () => {
    try {
      const results = await fetchJson(`/api/players/search?q=${encodeURIComponent(query)}`);
      renderPlayerResults(results);
    } catch (error) {
      playerResults.hidden = true;
    }
  }, 250);
});

function renderPlayerResults(results) {
  playerResults.innerHTML = "";
  if (!results.length) {
    playerResults.hidden = true;
    return;
  }
  for (const row of results) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${row.personaname} (${row.account_id})`;
    button.addEventListener("click", () => selectPlayer(row));
    item.append(button);
    playerResults.append(item);
  }
  playerResults.hidden = false;
}

async function selectPlayer(row) {
  playerInput.value = row.personaname;
  selectedAccountId = row.account_id;
  playerResults.hidden = true;
  await loadRecentMatches(row.account_id);
}

async function loadRecentMatches(accountId) {
  recent.hidden = true;
  recentList.innerHTML = "";
  try {
    const matches = await fetchJson(`/api/players/${accountId}/recent-matches`);
    if (!matches.length) {
      return;
    }
    for (const match of matches) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `match-chip ${match.won ? "win" : match.won === false ? "loss" : ""}`;
      const result = match.won ? "Win" : match.won === false ? "Loss" : "Match";
      button.innerHTML = `<strong>${escapeHtml(match.hero || "Unknown hero")}</strong><br>${result} ${match.kills}/${match.deaths}/${match.assists}<br>#${match.match_id}`;
      button.addEventListener("click", () => {
        matchInput.value = match.match_id;
      });
      recentList.append(button);
    }
    recent.hidden = false;
  } catch (error) {
    setStatus(error.message, true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  output.hidden = true;
  submitBtn.disabled = true;
  setStatus("Pulling the match and writing a plan...");
  const player = selectedAccountId ? String(selectedAccountId) : playerInput.value.trim();
  try {
    const payload = await fetchJson("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player,
        match_id: Number(matchInput.value),
      }),
    });
    renderReport(payload);
    setStatus("Done.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    submitBtn.disabled = false;
  }
});

function listHtml(items) {
  if (!items || !items.length) {
    return "<p>None called out.</p>";
  }
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderReport({ brief, report }) {
  const focus = brief.focus_player || {};
  const teamClass = focus.team === "Radiant" ? "radiant" : focus.team === "Dire" ? "dire" : "";
  const result = focus.won ? "Win" : focus.won === false ? "Loss" : "Unknown result";
  output.innerHTML = `
    <div class="meta">
      <span class="grade">${escapeHtml(report.grade)}</span>
      <div>
        <p class="headline">${escapeHtml(report.headline)}</p>
        <p>
          <span class="${teamClass}">${escapeHtml(focus.name || "Player")}</span>
          as ${escapeHtml(focus.hero || "unknown hero")}
          · ${escapeHtml(result)}
          · ${escapeHtml(brief.duration || "?")}
          · Match ${escapeHtml(brief.match_id)}
        </p>
      </div>
    </div>
    <p>${escapeHtml(report.match_read)}</p>
    <p>${escapeHtml(report.kda_context)}</p>
    <div class="grid">
      <article class="card">
        <h3>Strengths</h3>
        ${listHtml(report.strengths)}
      </article>
      <article class="card">
        <h3>Leaks</h3>
        ${listHtml(report.mistakes)}
      </article>
    </div>
    <div class="grid" style="margin-top: 12px">
      ${(report.focus_areas || [])
        .map(
          (area) => `
        <article class="card focus">
          <h3>${escapeHtml(area.title)}</h3>
          <p>${escapeHtml(area.why_it_matters)}</p>
          <p>${escapeHtml(area.how_to_practice)}</p>
        </article>`
        )
        .join("")}
      <article class="card">
        <h3>Next three games</h3>
        ${listHtml(report.next_three_games)}
      </article>
    </div>
  `;
  output.hidden = false;
}
