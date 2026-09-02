(function () {
  const panel = document.getElementById("settings");
  const toggleBtn = document.getElementById("settings-toggle");
  const bodyEl = document.getElementById("settings-body");
  const saveBtn = document.getElementById("settings-save");
  const noteEl = document.getElementById("settings-note");

  let state = null;
  let onError = () => {};

  function setNote(text, kind) {
    noteEl.textContent = text || "";
    noteEl.dataset.kind = kind || "";
  }

  function field(labelText, hintText, control) {
    const wrap = document.createElement("div");
    wrap.className = "setting";

    const label = document.createElement("label");
    label.className = "setting-label";
    label.textContent = labelText;
    label.setAttribute("for", control.id);

    wrap.appendChild(label);
    wrap.appendChild(control);

    if (hintText) {
      const hint = document.createElement("p");
      hint.className = "setting-hint";
      hint.textContent = hintText;
      wrap.appendChild(hint);
    }
    return wrap;
  }

  function select(id, options, current) {
    const el = document.createElement("select");
    el.id = id;
    el.className = "input";
    for (const option of options) {
      const opt = document.createElement("option");
      opt.value = typeof option === "string" ? option : option.value;
      opt.textContent = typeof option === "string" ? option : option.label;
      el.appendChild(opt);
    }
    el.value = current;
    return el;
  }

  function engineHeading(title, engine) {
    const head = document.createElement("div");
    head.className = "engine-head";

    const name = document.createElement("span");
    name.className = "engine-name";
    name.textContent = title;

    const tag = document.createElement("span");
    tag.className = "engine-tag";
    tag.textContent = engine;

    head.appendChild(name);
    head.appendChild(tag);
    return head;
  }

  function render() {
    bodyEl.innerHTML = "";

    // ---- speech to text -------------------------------------------------
    const stt = document.createElement("div");
    stt.className = "engine";
    stt.appendChild(engineHeading("Speech to text", state.stt.engine));
    stt.appendChild(
      field(
        "Model size",
        "Larger models transcribe more accurately but download more and run slower on CPU. A newly picked size downloads the first time you speak.",
        select("stt-model", state.stt.options, state.stt.model)
      )
    );
    bodyEl.appendChild(stt);

    // ---- language model -------------------------------------------------
    const llm = document.createElement("div");
    llm.className = "engine";
    llm.appendChild(engineHeading("Language model", state.llm.engine));

    if (state.llm.installed.length) {
      const options = state.llm.installed.slice();
      // Keep the configured model selectable even if it isn't pulled, so
      // opening settings never silently rewrites it to something else.
      if (!options.includes(state.llm.model)) {
        options.unshift(state.llm.model);
      }
      llm.appendChild(
        field(
          "Model",
          `Models already downloaded into Ollama at ${state.llm.base_url}. Download more from the list below.`,
          select("llm-model", options, state.llm.model)
        )
      );
      if (!state.llm.model_installed) {
        const warn = document.createElement("p");
        warn.className = "setting-warn";
        warn.textContent = `"${state.llm.model}" is not pulled yet — conversations will fail until you pull it or pick another model.`;
        llm.appendChild(warn);
      }
    } else {
      const input = document.createElement("input");
      input.id = "llm-model";
      input.className = "input";
      input.type = "text";
      input.value = state.llm.model;
      llm.appendChild(
        field(
          "Model",
          `Could not reach Ollama at ${state.llm.base_url}, so the installed models are unknown. You can still type a model name.`,
          input
        )
      );
    }
    llm.appendChild(renderCatalog());
    bodyEl.appendChild(llm);

    // ---- text to speech -------------------------------------------------
    const tts = document.createElement("div");
    tts.className = "engine";
    tts.appendChild(engineHeading("Voice", state.tts.engine));

    const hint = document.createElement("p");
    hint.className = "setting-hint";
    hint.textContent =
      "One voice per practice language. A newly picked voice downloads the first time it speaks.";
    tts.appendChild(hint);

    const grid = document.createElement("div");
    grid.className = "voice-grid";
    for (const entry of state.tts.voices) {
      const row = document.createElement("div");
      row.className = "voice-row";

      const label = document.createElement("label");
      label.className = "voice-lang";
      label.textContent = entry.label;
      label.setAttribute("for", `tts-${entry.code}`);

      row.appendChild(label);
      row.appendChild(select(`tts-${entry.code}`, entry.options, entry.voice));
      grid.appendChild(row);
    }
    tts.appendChild(grid);
    bodyEl.appendChild(tts);
  }

  function renderCatalog() {
    const wrap = document.createElement("div");
    wrap.className = "catalog";

    const head = document.createElement("p");
    head.className = "setting-label";
    head.textContent = "Available to download";
    wrap.appendChild(head);

    const free = state.llm.disk_free_gb;
    const ram = state.llm.ram_total_gb;
    const hint = document.createElement("p");
    hint.className = "setting-hint";
    let limits = "";
    if (free !== null && free !== undefined) limits += ` About ${free} GB disk free`;
    if (ram !== null && ram !== undefined) {
      limits += limits ? `, ${ram} GB RAM available.` : ` About ${ram} GB RAM available.`;
    } else if (limits) {
      limits += ".";
    }
    hint.textContent =
      "Bigger models speak other languages far better but need more disk and run slower on CPU." +
      limits;
    wrap.appendChild(hint);

    const pull = state.llm.pull || {};

    for (const model of state.llm.catalog) {
      const installed = state.llm.installed.includes(model.name);
      const busy = pull.status === "pulling";
      const isPulling = busy && pull.model === model.name;

      const row = document.createElement("div");
      row.className = "catalog-row";
      if (installed) row.classList.add("is-installed");

      const info = document.createElement("div");
      info.className = "catalog-info";

      const title = document.createElement("span");
      title.className = "catalog-name";
      title.textContent = `${model.label} · ${model.size_gb} GB`;
      if (model.multilingual) {
        const tag = document.createElement("span");
        tag.className = "catalog-flag";
        tag.textContent = "multilingual";
        title.appendChild(tag);
      }

      const note = document.createElement("span");
      note.className = "catalog-note";
      note.textContent = model.note;

      info.appendChild(title);
      info.appendChild(note);
      row.appendChild(info);

      if (installed) {
        // Installed is not the same as runnable: a model can sit on disk and
        // still be OOM-killed on load, which is worth flagging rather than
        // letting the user discover it as a 500 mid-conversation.
        const enoughRam =
          ram === null || ram === undefined || ram >= model.size_gb + 1.5;

        const done = document.createElement("span");
        done.className = enoughRam ? "catalog-installed" : "catalog-unrunnable";
        done.textContent = enoughRam ? "Installed" : "Installed · too big for RAM";
        if (!enoughRam) {
          done.title = `Needs roughly ${(model.size_gb + 1.5).toFixed(1)} GB of RAM to load, only ${ram} GB available. Raise Docker's memory limit or pick a smaller model.`;
          row.classList.add("is-too-big");
        }
        row.appendChild(done);
      } else if (isPulling) {
        const progress = document.createElement("span");
        progress.className = "catalog-progress";
        progress.textContent = `Downloading… ${pull.percent || 0}%`;
        row.appendChild(progress);
      } else {
        // Two separate limits, and a model has to clear both. Disk needs a
        // little headroom to unpack; RAM has to hold the weights at load time
        // or Ollama is OOM-killed after the download has already finished.
        const fitsDisk =
          free === null || free === undefined || free >= model.size_gb + 0.5;
        const fitsRam =
          ram === null || ram === undefined || ram >= model.size_gb + 1.5;
        const fits = fitsDisk && fitsRam;

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-ghost btn-sm";
        btn.textContent = fits
          ? "Download"
          : fitsDisk
            ? "Not enough memory"
            : "Not enough space";
        btn.disabled = busy || !fits;
        if (fits) {
          btn.addEventListener("click", () => pullModel(model.name));
        } else {
          btn.title = fitsDisk
            ? `Needs roughly ${(model.size_gb + 1.5).toFixed(1)} GB of RAM to load, only ${ram} GB available.`
            : `Needs about ${model.size_gb} GB of disk, only ${free} GB free.`;
          row.classList.add("is-too-big");
        }
        row.appendChild(btn);
      }

      wrap.appendChild(row);
    }

    if (pull.status === "error" && pull.error) {
      const err = document.createElement("p");
      err.className = "setting-warn";
      err.textContent = pull.error;
      wrap.appendChild(err);
    }

    return wrap;
  }

  async function pullModel(name) {
    setNote(`Starting download of ${name}…`, "");
    try {
      const response = await fetch("/api/models/llm/pull", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: name }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Could not start the download.`);
      }
      state.llm.pull = await response.json();
      render();
      pollPull();
    } catch (err) {
      setNote(err.message, "error");
    }
  }

  // A multi-GB pull runs on the backend; poll until it settles so the row can
  // show progress without holding a request open.
  function pollPull() {
    clearTimeout(pollPull.timer);
    pollPull.timer = setTimeout(async () => {
      try {
        const pull = await (await fetch("/api/models/llm/pull")).json();
        state.llm.pull = pull;

        if (pull.status === "pulling") {
          render();
          pollPull();
          return;
        }

        if (pull.status === "done") {
          setNote(`${pull.model} downloaded. You can select it above.`, "ok");
        } else if (pull.status === "error") {
          setNote(pull.error || "The download failed.", "error");
        }
        await load(); // refresh installed list + current selection
      } catch (err) {
        setNote("Lost track of the download. Reopen this panel to check.", "error");
      }
    }, 1500);
  }

  async function load() {
    const response = await fetch("/api/models");
    if (!response.ok) {
      throw new Error(`failed to load models: HTTP ${response.status}`);
    }
    state = await response.json();
    render();
  }

  function collect() {
    const payload = {
      stt_model: document.getElementById("stt-model").value,
      llm_model: document.getElementById("llm-model").value,
      tts_voices: {},
    };
    for (const entry of state.tts.voices) {
      payload.tts_voices[entry.code] = document.getElementById(
        `tts-${entry.code}`
      ).value;
    }
    return payload;
  }

  async function save() {
    saveBtn.disabled = true;
    setNote("Saving…", "");
    try {
      const response = await fetch("/api/models", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collect()),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Could not save (HTTP ${response.status}).`);
      }
      state = await response.json();
      render();
      setNote("Saved. New models are used from your next turn onwards.", "ok");
    } catch (err) {
      setNote(err.message, "error");
    } finally {
      saveBtn.disabled = false;
    }
  }

  async function toggle() {
    const opening = panel.hidden;
    if (!opening) {
      panel.hidden = true;
      toggleBtn.setAttribute("aria-expanded", "false");
      return;
    }

    setNote("", "");
    try {
      await load();
      panel.hidden = false;
      toggleBtn.setAttribute("aria-expanded", "true");
    } catch (err) {
      onError("Could not load the model settings. Is the backend running?");
    }
  }

  function init(options) {
    onError = (options && options.onError) || onError;
    toggleBtn.addEventListener("click", toggle);
    saveBtn.addEventListener("click", save);
  }

  window.Settings = { init };
})();
