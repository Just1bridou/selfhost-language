(function () {
  const listEl = document.getElementById("scenario-list");
  const startBtn = document.getElementById("start-session-btn");
  const languageEl = document.getElementById("language-options");

  // Small visual cue per built-in scenario. Unknown ids fall back to a
  // neutral glyph, so adding a scenario never needs a change here.
  const SCENARIO_GLYPHS = {
    restaurant: "🍽",
    "job-interview": "💼",
    "small-talk": "💬",
    "asking-directions": "🧭",
    shopping: "🛍",
  };
  const DEFAULT_GLYPH = "🗣";

  let selectedScenario = null;
  let selectedLanguage = null;

  // Both a language and a scenario are required before a session can start,
  // so the AI always knows which language to speak.
  function refreshStartButton() {
    startBtn.disabled = !(selectedScenario && selectedLanguage);
  }

  // CSS uses :has(input:checked) for the selected look; this class mirrors it
  // so the UI still reads correctly on engines without :has() support.
  function markSelected(container, selector, chosenEl) {
    for (const el of container.querySelectorAll(selector)) {
      el.classList.toggle("is-selected", el === chosenEl);
    }
  }

  async function fetchJson(path, what) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`failed to load ${what}: HTTP ${response.status}`);
    }
    return response.json();
  }

  function renderLanguages(languages) {
    languageEl.innerHTML = "";
    for (const language of languages) {
      const pill = document.createElement("label");
      pill.className = "pill";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "language";
      radio.value = language.code;
      radio.addEventListener("change", () => {
        selectedLanguage = language;
        markSelected(languageEl, ".pill", pill);
        refreshStartButton();
      });

      pill.appendChild(radio);
      pill.appendChild(document.createTextNode(language.native_label));
      languageEl.appendChild(pill);
    }
  }

  function renderScenarios(scenarios) {
    listEl.innerHTML = "";
    for (const scenario of scenarios) {
      const card = document.createElement("label");
      card.className = "scenario-card";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "scenario";
      radio.value = scenario.id;
      radio.addEventListener("change", () => {
        selectedScenario = scenario;
        markSelected(listEl, ".scenario-card", card);
        refreshStartButton();
      });

      const glyph = document.createElement("span");
      glyph.className = "scenario-glyph";
      glyph.setAttribute("aria-hidden", "true");
      glyph.textContent = SCENARIO_GLYPHS[scenario.id] || DEFAULT_GLYPH;

      const body = document.createElement("span");
      body.className = "scenario-body";

      const name = document.createElement("span");
      name.className = "scenario-name";
      name.textContent = scenario.title;

      const meta = document.createElement("span");
      meta.className = "scenario-meta";
      meta.textContent = scenario.difficulty;

      body.appendChild(name);
      body.appendChild(meta);

      card.appendChild(radio);
      card.appendChild(glyph);
      card.appendChild(body);
      listEl.appendChild(card);
    }
  }

  function renderLoadError(onRetry) {
    languageEl.innerHTML = "";
    listEl.innerHTML = "";

    const box = document.createElement("div");
    box.className = "scenario-empty";
    box.appendChild(
      document.createTextNode("Could not load the options. Is the backend running?")
    );

    const retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.className = "btn btn-ghost btn-sm";
    retryBtn.textContent = "Retry";
    retryBtn.addEventListener("click", onRetry);

    box.appendChild(retryBtn);
    listEl.appendChild(box);
  }

  async function loadOptions() {
    try {
      const [languages, scenarios] = await Promise.all([
        fetchJson("/api/languages", "languages"),
        fetchJson("/api/scenarios", "scenarios"),
      ]);
      renderLanguages(languages);
      renderScenarios(scenarios);
    } catch (err) {
      renderLoadError(loadOptions);
    }
  }

  async function init(onStart) {
    await loadOptions();

    startBtn.addEventListener("click", () => {
      if (selectedScenario && selectedLanguage) {
        onStart({
          scenarioId: selectedScenario.id,
          scenarioTitle: selectedScenario.title,
          language: selectedLanguage.code,
          languageLabel: selectedLanguage.native_label,
        });
      }
    });
  }

  function reset() {
    selectedScenario = null;
    selectedLanguage = null;
    startBtn.disabled = true;

    for (const input of document.querySelectorAll(
      "#language-options input:checked, #scenario-list input:checked"
    )) {
      input.checked = false;
    }
    markSelected(languageEl, ".pill", null);
    markSelected(listEl, ".scenario-card", null);
  }

  window.ScenarioPicker = { init, reset };
})();
