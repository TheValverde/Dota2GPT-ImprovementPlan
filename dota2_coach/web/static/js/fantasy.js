const spanAmount = document.getElementById("span-amount");
const spanUnit = document.getElementById("span-unit");
const refreshBtn = document.getElementById("refresh-fantasy");
const fantasyPlayer = document.getElementById("fantasy-player");
const fantasyResults = document.getElementById("fantasy-results");
const fantasyStatus = document.getElementById("fantasy-status");
const rosterEl = document.getElementById("roster");
const detailEl = document.getElementById("player-detail");

let selectedTrackedId = null;
let fantasyLoaded = false;

function spanParams() {
  return {
    amount: Number(spanAmount.value) || 7,
    unit: spanUnit.value,
  };
}

function setFantasyStatus(message, isError = false) {
  fantasyStatus.textContent = message;
  fantasyStatus.classList.toggle("error", isError);
}

function sparkHtml(values) {
  if (!values.length) {
    return '<div class="spark empty"></div>';
  }
  const max = Math.max(...values, 1);
  return `<div class="spark">${values
    .map((value) => {
      const height = Math.max(8, Math.round((value / max) * 100));
      return `<span style="height:${height}%"></span>`;
    })
    .join("")}</div>`;
}

async function loadRoster() {
  const span = spanParams();
  const data = await fetchJson(`/api/fantasy/roster?amount=${span.amount}&unit=${span.unit}`);
  if (!data.players.length) {
    rosterEl.innerHTML = '<p class="empty-copy">Add players to start a fantasy board.</p>';
    detailEl.hidden = true;
    return data;
  }
  rosterEl.innerHTML = data.players
    .map(
      (player) => `
      <article class="roster-card ${player.account_id === selectedTrackedId ? "is-selected" : ""}" data-id="${player.account_id}">
        <div>
          <h3>${escapeHtml(player.personaname)}</h3>
          <p>${escapeHtml(player.rank || "Unranked")} · ${player.match_count} matches</p>
        </div>
        <div class="score-block">
          <p class="total">${player.total.toFixed(1)}</p>
          <p>avg ${player.average.toFixed(1)}</p>
        </div>
        ${sparkHtml(player.sparkline || [])}
        <button type="button" class="ghost remove" data-remove="${player.account_id}">Remove</button>
      </article>`
    )
    .join("");
  rosterEl.querySelectorAll(".roster-card").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("[data-remove]")) {
        return;
      }
      selectedTrackedId = Number(card.dataset.id);
      loadPlayerDetail(selectedTrackedId);
      loadRoster().catch(() => {});
    });
  });
  rosterEl.querySelectorAll("[data-remove]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const accountId = Number(button.dataset.remove);
      await fetchJson(`/api/fantasy/roster/${accountId}`, { method: "DELETE" });
      if (selectedTrackedId === accountId) {
        selectedTrackedId = null;
        detailEl.hidden = true;
      }
      await loadRoster();
    });
  });
  return data;
}

async function loadPlayerDetail(accountId) {
  const span = spanParams();
  const player = await fetchJson(`/api/fantasy/players/${accountId}?amount=${span.amount}&unit=${span.unit}`);
  const matches = player.matches || [];
  detailEl.innerHTML = `
    <h2>${escapeHtml(player.personaname)}</h2>
    <p>${player.match_count} matches · total ${player.total.toFixed(1)} · avg ${player.average.toFixed(1)}</p>
    <div class="match-table">
      ${matches
        .map((match) => {
          const result = match.won ? "W" : match.won === false ? "L" : "-";
          return `<button type="button" class="match-row" data-match="${match.match_id}">
            <span>${escapeHtml(match.hero || "Hero")}</span>
            <span>${result} ${match.kills}/${match.deaths}/${match.assists}</span>
            <strong>${Number(match.points || 0).toFixed(1)}</strong>
          </button>`;
        })
        .join("")}
    </div>
  `;
  detailEl.hidden = false;
  detailEl.querySelectorAll("[data-match]").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById("match-id").value = button.dataset.match;
      document.getElementById("player").value = String(accountId);
      document.querySelector('.tab[data-tab="coach"]').click();
    });
  });
}

bindPlayerSearch(fantasyPlayer, fantasyResults, async (row) => {
  fantasyPlayer.value = "";
  setFantasyStatus(`Adding ${row.personaname}...`);
  const span = spanParams();
  try {
    await fetchJson("/api/fantasy/roster", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: row.account_id, ...span }),
    });
    selectedTrackedId = row.account_id;
    await loadRoster();
    await loadPlayerDetail(row.account_id);
    setFantasyStatus(`Tracking ${row.personaname}.`);
  } catch (error) {
    setFantasyStatus(error.message, true);
  }
});

fantasyPlayer.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") {
    return;
  }
  const value = fantasyPlayer.value.trim();
  if (!/^\d+$/.test(value)) {
    return;
  }
  event.preventDefault();
  const span = spanParams();
  setFantasyStatus("Adding account...");
  try {
    await fetchJson("/api/fantasy/roster", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: Number(value), ...span }),
    });
    fantasyPlayer.value = "";
    selectedTrackedId = Number(value);
    await loadRoster();
    await loadPlayerDetail(Number(value));
    setFantasyStatus("Player added.");
  } catch (error) {
    setFantasyStatus(error.message, true);
  }
});

refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  setFantasyStatus("Refreshing OpenDota matches...");
  try {
    const span = spanParams();
    await fetchJson("/api/fantasy/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(span),
    });
    await loadRoster();
    if (selectedTrackedId) {
      await loadPlayerDetail(selectedTrackedId);
    }
    setFantasyStatus("Roster updated.");
  } catch (error) {
    setFantasyStatus(error.message, true);
  } finally {
    refreshBtn.disabled = false;
  }
});

spanAmount.addEventListener("change", () => loadRoster().catch((error) => setFantasyStatus(error.message, true)));
spanUnit.addEventListener("change", () => loadRoster().catch((error) => setFantasyStatus(error.message, true)));

document.addEventListener("fantasy-shown", async () => {
  if (fantasyLoaded) {
    await loadRoster();
    return;
  }
  fantasyLoaded = true;
  try {
    await loadRoster();
  } catch (error) {
    setFantasyStatus(error.message, true);
  }
});
