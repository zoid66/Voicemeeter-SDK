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

function log(message, isError = false) {
  activityLog.textContent = message;
  activityLog.classList.toggle("error", isError);
}

function channelCard(kind, index) {
  const prefix = `${kind}[${index}]`;
  const label = kind === "Strip" ? `Input ${index + 1}` : `Bus ${index + 1}`;
  const card = document.createElement("article");
  card.className = "channel";
  card.innerHTML = `
    <div class="channel-name">${label}<span class="channel-number">${prefix}</span></div>
    <div class="meter"><div class="meter-fill"></div></div>
    <input class="gain" type="range" min="-60" max="12" step="0.1" value="0" aria-label="${label} gain">
    <div class="gain-value">0.0 dB</div>
    <div class="toggle-row">
      <button class="toggle" data-param="${prefix}.Mute">Mute</button>
      ${kind === "Strip" ? `<button class="toggle" data-param="${prefix}.Mono">Mono</button>` : ""}
    </div>`;
  const slider = card.querySelector(".gain");
  const value = card.querySelector(".gain-value");
  slider.addEventListener("input", () => {
    value.textContent = `${Number(slider.value).toFixed(1)} dB`;
  });
  slider.addEventListener("change", () =>
    setParameter(`${prefix}.Gain`, slider.value),
  );
  card.querySelectorAll(".toggle").forEach((button) => {
    button.addEventListener("click", async () => {
      button.classList.toggle("active");
      const result = await setParameter(
        button.dataset.param,
        button.classList.contains("active") ? 1 : 0,
      );
      if (!result.ok) button.classList.toggle("active");
    });
  });
  return card;
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
setInterval(refreshStatus, 2500);
