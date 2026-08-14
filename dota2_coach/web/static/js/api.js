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
    const detail = payload.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status})`);
  }
  return payload;
}

function bindPlayerSearch(input, list, onPick) {
  let timer = null;
  input.addEventListener("input", () => {
    const query = input.value.trim();
    window.clearTimeout(timer);
    if (query.length < 2) {
      list.hidden = true;
      list.innerHTML = "";
      return;
    }
    if (/^\d+$/.test(query)) {
      list.hidden = true;
      return;
    }
    timer = window.setTimeout(async () => {
      try {
        const results = await fetchJson(`/api/players/search?q=${encodeURIComponent(query)}`);
        list.innerHTML = "";
        if (!results.length) {
          list.hidden = true;
          return;
        }
        for (const row of results) {
          const item = document.createElement("li");
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = `${row.personaname} (${row.account_id})`;
          button.addEventListener("click", () => {
            list.hidden = true;
            onPick(row);
          });
          item.append(button);
          list.append(item);
        }
        list.hidden = false;
      } catch (error) {
        list.hidden = true;
      }
    }, 250);
  });
}
