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

const rankedOnly = document.getElementById("ranked-only");
const hideTurbo = document.getElementById("hide-turbo");

function spanParams() {
  return {
    amount: Number(spanAmount.value) || 7,
    unit: spanUnit.value,
    ranked_only: rankedOnly.checked,
    hide_turbo: hideTurbo.checked,
  };
}

function spanQuery() {
  const span = spanParams();
  return new URLSearchParams({
    amount: String(span.amount),
    unit: span.unit,
    ranked_only: String(span.ranked_only),
    hide_turbo: String(span.hide_turbo),
  }).toString();
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
  const data = await fetchJson(`/api/fantasy/roster?${spanQuery()}`);
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
  const player = await fetchJson(`/api/fantasy/players/${accountId}?${spanQuery()}`);
  const field = await fetchJson(
    `/api/fantasy/players/${accountId}/field?amount=${span.amount}&unit=${span.unit}&hide_turbo=${span.hide_turbo}`
  );
  renderPlayerDetail(player, field);
  if ((field.unparsed_match_ids || []).length) {
    requestMissingParses(accountId, field).catch((error) => setFantasyStatus(error.message, true));
  }
}

function renderPlayerDetail(player, field) {
  const matches = player.matches || [];
  detailEl.innerHTML = `
    <h2>${escapeHtml(player.personaname)}</h2>
    <p>${player.match_count} matches · total ${player.total.toFixed(1)} · avg ${player.average.toFixed(1)}</p>
    ${fieldHtml(field)}
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
      document.getElementById("player").value = String(player.account_id);
      document.querySelector('.tab[data-tab="coach"]').click();
    });
  });
  const parseBtn = document.getElementById("parse-ranked");
  if (parseBtn) {
    parseBtn.addEventListener("click", () => {
      requestMissingParses(player.account_id, field).catch((error) =>
        setFantasyStatus(error.message, true)
      );
    });
  }
}

function fieldHtml(field) {
  if (!field || !field.players || !field.players.length) {
    return `<section class="field-box"><h3>Ranked field</h3><p class="muted">No ranked lobbies in this span.</p></section>`;
  }
  const you = field.you || {};
  const duo = field.duo;
  const unparsed = (field.unparsed_match_ids || []).length;
  const parseNote = unparsed
    ? `<p class="muted">${unparsed} ranked replay${unparsed === 1 ? " is" : "s are"} unparsed. Ward and stun points are incomplete until OpenDota finishes.</p>
       <button type="button" id="parse-ranked">Parse unparsed ranked</button>`
    : `<p class="muted">${field.parsed_matches} ranked ${field.parsed_matches === 1 ? "replay is" : "replays are"} parsed.</p>`;
  const duoLine = duo
    ? `<p>Duo: <strong>${escapeHtml(duo.personaname)}</strong> · ${duo.teammate_games} games as teammate · avg ${duo.average.toFixed(1)}</p>`
    : `<p class="muted">No duo yet (needs 2+ ranked games on your team).</p>`;
  const rows = (field.regulars || field.players)
    .map((row) => {
      const tag = row.relation === "you" ? "You" : row.relation === "duo" ? "Duo" : row.relation === "stack" ? "Stack" : row.relation === "enemy" ? "Enemy" : row.relation === "teammate" ? "Team" : "Lobby";
      return `<button type="button" class="field-row ${row.is_focus ? "is-you" : ""} ${row.is_duo ? "is-duo" : ""}" data-field-id="${row.account_id}">
        <span class="field-rank">${row.rank}</span>
        <span>${escapeHtml(row.personaname)}</span>
        <span class="badge">${tag}</span>
        <span>${row.games}g · ${row.teammate_games} with you</span>
        <strong>${row.average.toFixed(1)}</strong>
      </button>`;
    })
    .join("");
  return `<section class="field-box">
    <h3>Ranked field</h3>
    <p>Same ranked lobbies only. You are ${you.rank || "-"} of ${field.players.length} by average (${Number(you.average || 0).toFixed(1)}) over ${field.match_count} games.</p>
    ${duoLine}
    ${parseNote}
    <div class="field-table">${rows}</div>
    ${
      field.one_game_players
        ? `<p class="muted">${field.one_game_players} other players appeared in only one ranked lobby with you. Cores in a single stomp will outscore a support average, so they stay off this table.</p>`
        : ""
    }
  </section>`;
}

const requestedParses = new Set();

async function requestMissingParses(accountId, field) {
  const pending = (field.unparsed_match_ids || []).filter((id) => !requestedParses.has(id));
  if (!pending.length) {
    return;
  }
  pending.forEach((id) => requestedParses.add(id));
  const parseBtn = document.getElementById("parse-ranked");
  if (parseBtn) {
    parseBtn.disabled = true;
  }
  const span = spanParams();
  try {
    setFantasyStatus("Requesting OpenDota parses for unparsed ranked replays...");
    const started = await fetchJson(
      `/api/fantasy/players/${accountId}/parse-missing?amount=${span.amount}&unit=${span.unit}&hide_turbo=${span.hide_turbo}`,
      { method: "POST" }
    );
    const jobs = (started.jobs || []).filter((job) => job.job_id);
    if (!jobs.length) {
      setFantasyStatus(started.message || "No parse jobs queued.");
      return;
    }
    setFantasyStatus(`Waiting on ${jobs.length} parse job${jobs.length === 1 ? "" : "s"}...`);
    const deadline = Date.now() + 60000;
    while (Date.now() < deadline) {
      await new Promise((resolve) => window.setTimeout(resolve, 4000));
      let remaining = 0;
      for (const job of jobs) {
        const status = await fetchJson(
          `/api/matches/${job.match_id}/parse-status?job_id=${encodeURIComponent(job.job_id)}`
        );
        if (!status.parsed && status.queued) {
          remaining += 1;
        }
      }
      if (!remaining) {
        break;
      }
      setFantasyStatus(`Still parsing ${remaining} ranked replay${remaining === 1 ? "" : "s"}...`);
    }
    await loadRoster();
    const player = await fetchJson(`/api/fantasy/players/${accountId}?${spanQuery()}`);
    const refreshed = await fetchJson(
      `/api/fantasy/players/${accountId}/field?amount=${span.amount}&unit=${span.unit}&hide_turbo=${span.hide_turbo}`
    );
    renderPlayerDetail(player, refreshed);
    const left = (refreshed.unparsed_match_ids || []).length;
    if (left) {
      setFantasyStatus(`Parsed what OpenDota finished. ${left} ranked replay${left === 1 ? " is" : "s are"} still unparsed.`);
    } else {
      setFantasyStatus("Ranked field updated with parsed replays.");
    }
  } catch (error) {
    pending.forEach((id) => requestedParses.delete(id));
    throw error;
  }
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

async function reloadFantasyBoard() {
  await loadRoster();
  if (selectedTrackedId) {
    await loadPlayerDetail(selectedTrackedId);
  }
}

spanAmount.addEventListener("change", () =>
  reloadFantasyBoard().catch((error) => setFantasyStatus(error.message, true))
);
spanUnit.addEventListener("change", () =>
  reloadFantasyBoard().catch((error) => setFantasyStatus(error.message, true))
);
rankedOnly.addEventListener("change", () =>
  reloadFantasyBoard().catch((error) => setFantasyStatus(error.message, true))
);
hideTurbo.addEventListener("change", () =>
  reloadFantasyBoard().catch((error) => setFantasyStatus(error.message, true))
);

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
