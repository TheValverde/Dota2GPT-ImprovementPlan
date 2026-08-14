const tabs = document.querySelectorAll(".tab");
const panels = {
  coach: document.getElementById("panel-coach"),
  fantasy: document.getElementById("panel-fantasy"),
};
const pinBtn = document.getElementById("pin-btn");
const minBtn = document.getElementById("min-btn");
const closeBtn = document.getElementById("close-btn");

let pinned = false;
let isDesktop = Boolean(window.pywebview);

document.body.classList.toggle("is-desktop", isDesktop);

window.addEventListener("pywebviewready", () => {
  isDesktop = true;
  document.body.classList.add("is-desktop");
});

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const name = tab.dataset.tab;
    tabs.forEach((item) => item.classList.toggle("is-active", item === tab));
    Object.entries(panels).forEach(([key, panel]) => {
      panel.hidden = key !== name;
    });
    if (name === "fantasy") {
      document.dispatchEvent(new CustomEvent("fantasy-shown"));
    }
  });
});

async function desktop(method, ...args) {
  if (!window.pywebview?.api?.[method]) {
    return null;
  }
  return window.pywebview.api[method](...args);
}

pinBtn.addEventListener("click", async () => {
  pinned = !pinned;
  await desktop("set_on_top", pinned);
  pinBtn.classList.toggle("is-active", pinned);
  pinBtn.textContent = pinned ? "Pinned" : "Pin";
});

minBtn.addEventListener("click", () => desktop("minimize"));
closeBtn.addEventListener("click", () => {
  if (isDesktop) {
    desktop("close");
  } else {
    window.close();
  }
});
