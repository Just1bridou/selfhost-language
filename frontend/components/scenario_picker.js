(function () {
  const listEl = document.getElementById("scenario-list");
  const startBtn = document.getElementById("start-session-btn");

  let selectedScenarioId = null;

  async function fetchScenarios() {
    const response = await fetch("/api/scenarios");
    if (!response.ok) {
      throw new Error(`failed to load scenarios: HTTP ${response.status}`);
    }
    return response.json();
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
        startBtn.disabled = false;
      });
      label.appendChild(radio);
      label.appendChild(
        document.createTextNode(` ${scenario.title} (${scenario.difficulty})`)
      );
      item.appendChild(label);
      listEl.appendChild(item);
    }
  }

  function renderLoadError() {
    listEl.innerHTML = "";
    const item = document.createElement("li");
    item.textContent = "Could not load scenarios. Is the backend running?";
    listEl.appendChild(item);
  }

  async function init(onStart) {
    try {
      const scenarios = await fetchScenarios();
      renderScenarios(scenarios);
    } catch (err) {
      renderLoadError();
    }

    startBtn.addEventListener("click", () => {
      if (selectedScenarioId) {
        onStart(selectedScenarioId);
      }
    });
  }

  window.ScenarioPicker = { init };
})();
