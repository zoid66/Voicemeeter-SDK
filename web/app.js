const stripCount = 8;
const busCount = 8;
const stripBank = document.querySelector("#strip-bank");
const busBank = document.querySelector("#bus-bank");
const statusDot = document.querySelector("#status-dot");
const statusText = document.querySelector("#status-text");
const connectButton = document.querySelector("#connect-button");
const engineValue = document.querySelector("#engine-value");
const engineMeta = document.querySelector("#engine-meta");
const activityLog = document.querySelector("#activity-log");

const channelCards = new Map();
const gainValues = new Map();
let linkSelection = [];
let linkedPair = [];
let activeGainDrag = false;
let linkedUpdateFrame = null;
let pendingLinkedValues = null;
let syncInProgress = false;

function log(message, isError = false) {
  activityLog.textContent = message;
  activityLog.classList.toggle("error", isError);
}

function channelCard(kind, index) {
  const prefix = `${kind}[${index}]`;
  const label = kind === "Strip" ? `Input ${index + 1}` : `Bus ${index + 1}`;
  gainValues.set(prefix, 0);
  const card = document.createElement("article");
  card.className = "channel";
  card.dataset.channel = prefix;
  card.innerHTML = `
    <div class="channel-name">${label}<span class="channel-number">${prefix}</span></div>
    <div class="meter"><div class="meter-fill"></div></div>
    <input class="gain" type="range" min="-60" max="12" step="0.1" value="0" aria-label="${label} gain">
    <div class="gain-value">0.0 dB</div>
    <div class="toggle-row">
      <button class="toggle" data-param="${prefix}.Mute">Mute</button>
      ${kind === "Strip" ? `<button class="toggle" data-param="${prefix}.Mono">Mono</button>` : ""}
      <button class="toggle link-button" data-link="${prefix}">Link</button>
    </div>`;
  const slider = card.querySelector(".gain");
  const value = card.querySelector(".gain-value");
  slider.addEventListener("input", () => {
    updateGain(prefix, Number(slider.value));
  });
  slider.addEventListener("pointerdown", () => {
    activeGainDrag = true;
  });
  slider.addEventListener("change", () => {
    updateGain(prefix, Number(slider.value), true);
  });
  card.querySelectorAll(".toggle").forEach((button) => {
    if (button.classList.contains("link-button")) {
      button.addEventListener("click", () => toggleLink(prefix));
      return;
    }
    button.addEventListener("click", async () => {
      button.classList.toggle("active");
      const result = await setParameter(
        button.dataset.param,
        button.classList.contains("active") ? 1 : 0,
      );
      if (!result.ok) button.classList.toggle("active");
    });
  });
  channelCards.set(prefix, card);
  return card;
}

function clampGain(gain) {
  return Math.min(12, Math.max(-60, gain));
}

function setGainDisplay(prefix, gain) {
  const card = channelCards.get(prefix);
  if (!card) return;
  const slider = card.querySelector(".gain");
  const value = card.querySelector(".gain-value");
  const normalizedGain = clampGain(gain);
  slider.value = normalizedGain.toFixed(1);
  value.textContent = `${normalizedGain.toFixed(1)} dB`;
  gainValues.set(prefix, normalizedGain);
}

function updateGain(prefix, gain, force = false) {
  const sourceGain = clampGain(gain);
  const previousGain = gainValues.get(prefix) ?? 0;
  setGainDisplay(prefix, sourceGain);

  if (!linkedPair.includes(prefix)) {
    if (force) setParameter(`${prefix}.Gain`, sourceGain);
    return;
  }

  const delta = sourceGain - previousGain;
  const partner = linkedPair.find((name) => name !== prefix);
  if (!partner || Math.abs(delta) < 0.0001) return;
  const partnerGain = clampGain((gainValues.get(partner) ?? 0) + delta);
  setGainDisplay(partner, partnerGain);
  queueLinkedUpdate([
    { name: `${prefix}.Gain`, value: sourceGain },
    { name: `${partner}.Gain`, value: partnerGain },
  ]);
}

function toggleLink(prefix) {
  if (linkedPair.includes(prefix)) {
    unlinkPair();
    return;
  }

  if (linkedPair.length === 2) unlinkPair();

  linkSelection.push(prefix);
  if (linkSelection.length === 1) {
    updateLinkButtons();
    log(`${prefix} selected; choose a second channel to link`);
    return;
  }

  if (linkSelection.length === 2 && linkSelection[0] !== linkSelection[1]) {
    linkedPair = [...linkSelection];
    linkSelection = [];
    updateLinkButtons();
    log(`${linkedPair[0]} and ${linkedPair[1]} linked with offset preserved`);
    return;
  }

  linkSelection = [];
  updateLinkButtons();
}

function unlinkPair() {
  linkedPair = [];
  linkSelection = [];
  updateLinkButtons();
  log("Linked gains unlinked");
}

function updateLinkButtons() {
  channelCards.forEach((card, prefix) => {
    const button = card.querySelector(".link-button");
    button.classList.toggle("active", linkedPair.includes(prefix));
    button.classList.toggle("selecting", linkSelection.includes(prefix));
    button.textContent =
      linkedPair.includes(prefix) || linkSelection.includes(prefix)
        ? "Linked"
        : "Link";
  });
}

function queueLinkedUpdate(values) {
  pendingLinkedValues = values;
  if (linkedUpdateFrame !== null) return;
  linkedUpdateFrame = requestAnimationFrame(async () => {
    linkedUpdateFrame = null;
    const valuesToSend = pendingLinkedValues;
    pendingLinkedValues = null;
    if (!valuesToSend || !window.pywebview) return;
    const result =
      await window.pywebview.api.set_linked_parameters(valuesToSend);
    if (!result.ok) log(result.error, true);
    else log(
      `${valuesToSend[0].name} and ${valuesToSend[1].name} linked gain updated`,
    );
  });
}

async function syncGainValues() {
  if (!window.pywebview || activeGainDrag || linkSelection.length > 0 || syncInProgress) return;
  syncInProgress = true;
  try {
    for (const [prefix] of channelCards) {
      const result = await window.pywebview.api.get_parameter(`${prefix}.Gain`);
      if (result.ok) setGainDisplay(prefix, result.value);
    }
  } finally {
    syncInProgress = false;
  }
}

for (let index = 0; index < stripCount; index += 1)
  stripBank.appendChild(channelCard("Strip", index));
for (let index = 0; index < busCount; index += 1)
  busBank.appendChild(channelCard("Bus", index));

async function setParameter(name, value) {
  if (!window.pywebview) return { ok: false, error: "PyWebView is not ready" };
  const result = await window.pywebview.api.set_parameter(name, Number(value));
  if (!result.ok) log(result.error, true);
  else log(`${name} set to ${value}`);
  return result;
}

async function refreshStatus() {
  if (!window.pywebview) return;
  const state = await window.pywebview.api.status();
  statusDot.classList.toggle("connected", state.connected);
  statusText.textContent = state.connected ? state.message : "Disconnected";
  connectButton.textContent = state.connected ? "Disconnect" : "Connect";
  engineValue.textContent = state.connected
    ? `Type ${state.type}`
    : "Not connected";
  engineMeta.textContent = state.connected
    ? `Version ${state.version}`
    : state.message;
  if (state.connected) syncGainValues();
}

connectButton.addEventListener("click", async () => {
  const state =
    connectButton.textContent === "Connect"
      ? await window.pywebview.api.connect()
      : await window.pywebview.api.disconnect();
  log(
    state.message,
    !state.connected && connectButton.textContent === "Connect",
  );
  refreshStatus();
});

document.querySelector("#send-script").addEventListener("click", async () => {
  const script = document.querySelector("#script-input").value;
  const result = await window.pywebview.api.execute_script(script);
  log(result.ok ? result.message : result.error, !result.ok);
});

window.addEventListener("pywebviewready", refreshStatus);
window.addEventListener("pointerup", () => {
  activeGainDrag = false;
});
window.addEventListener("pointercancel", () => {
  activeGainDrag = false;
});
setInterval(refreshStatus, 2500);
