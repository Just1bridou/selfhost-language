(function () {
  const listEl = document.getElementById("scenario-list");
  const startBtn = document.getElementById("start-session-btn");
  const languageSelect = document.getElementById("language-select");

  let selectedScenarioId = null;
  let selectedLanguage = null;

  // Both a language and a scenario are required before a session can start,
  // so the AI always knows which language to speak.
  function refreshStartButton() {
    startBtn.disabled = !(selectedScenarioId && selectedLanguage);
  }

  async function fetchJson(path, what) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`failed to load ${what}: HTTP ${response.status}`);
    }
    return response.json();
  }

  function renderLanguages(languages) {
    // Drop everything but the "— Choose a language —" placeholder, so a retry
    // after a failed load doesn't append a duplicate set of options.
    while (languageSelect.options.length > 1) {
      languageSelect.remove(1);
    }
    for (const language of languages) {
      const option = document.createElement("option");
      option.value = language.code;
      option.textContent =
        language.native_label === language.label
          ? language.label
          : `${language.native_label} (${language.label})`;
      languageSelect.appendChild(option);
    }
  }

  function renderScenarios(scenarios) {
    listEl.innerHTML = "";
    for (const scenario of scenarios) {
      const item = document.createElement("li");
      const label = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "scenario";
      radio.value = scenario.id;
      radio.addEventListener("change", () => {
        selectedScenarioId = scenario.id;
        refreshStartButton();
      });
      label.appendChild(radio);
      label.appendChild(
        document.createTextNode(` ${scenario.title} (${scenario.difficulty})`)
      );
      item.appendChild(label);
      listEl.appendChild(item);
    }
  }

  function renderLoadError(onRetry) {
    listEl.innerHTML = "";
    const item = document.createElement("li");
    item.textContent = "Could not load scenarios. Is the backend running? ";
    const retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.textContent = "Retry";
    retryBtn.addEventListener("click", onRetry);
    item.appendChild(retryBtn);
    listEl.appendChild(item);
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
    languageSelect.addEventListener("change", () => {
      selectedLanguage = languageSelect.value || null;
      refreshStartButton();
    });

    await loadOptions();

    startBtn.addEventListener("click", () => {
      if (selectedScenarioId && selectedLanguage) {
        onStart(selectedScenarioId, selectedLanguage);
      }
    });
  }

  function reset() {
    selectedScenarioId = null;
    selectedLanguage = null;
    languageSelect.selectedIndex = 0;
    startBtn.disabled = true;
    const checked = listEl.querySelector("input[type=radio]:checked");
    if (checked) {
      checked.checked = false;
    }
  }

  window.ScenarioPicker = { init, reset };
})();
