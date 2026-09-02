(function () {
  const mainEl = document.getElementById("main");
  const scenarioSection = document.getElementById("scenario-picker");
  const conversationSection = document.getElementById("conversation");
  const conversationHeader = conversationSection.querySelector(".conversation-header");
  const conversationTitle = document.getElementById("conversation-title");
  const statusEl = document.getElementById("status-indicator");
  const recordBtn = document.getElementById("record-btn");
  const replyAudio = document.getElementById("reply-audio");

  // Created here rather than in index.html: #conversation is already only
  // ever visible while a session is active, so putting this button inside it
  // makes it visible exactly when a session is running, with no extra
  // show/hide logic of its own.
  const endSessionBtn = document.createElement("button");
  endSessionBtn.id = "end-session-btn";
  endSessionBtn.type = "button";
  endSessionBtn.className = "btn btn-ghost btn-sm";
  endSessionBtn.textContent = "End session";
  conversationHeader.appendChild(endSessionBtn);

  // One shared, dismissible banner reused for every failure mode (mic
  // permission, turn failures, scenario/session-start failures) rather than
  // each one fighting over the status text. Sits above both sections so it's
  // visible whichever one is showing.
  const errorBanner = document.createElement("div");
  errorBanner.id = "error-banner";
  errorBanner.hidden = true;
  errorBanner.setAttribute("role", "alert");
  errorBanner.setAttribute("aria-live", "assertive");

  const errorIcon = document.createElement("span");
  errorIcon.className = "error-icon";
  errorIcon.setAttribute("aria-hidden", "true");
  errorIcon.textContent = "!";

  const errorText = document.createElement("span");
  errorText.className = "error-text";

  const errorDismissBtn = document.createElement("button");
  errorDismissBtn.type = "button";
  errorDismissBtn.className = "error-dismiss";
  errorDismissBtn.setAttribute("aria-label", "Dismiss error");
  errorDismissBtn.textContent = "×";

  errorBanner.append(errorIcon, errorText, errorDismissBtn);
  mainEl.insertBefore(errorBanner, mainEl.firstChild);

  function showError(message) {
    errorText.textContent = message;
    errorBanner.hidden = false;
  }

  function hideError() {
    errorBanner.hidden = true;
    errorText.textContent = "";
  }

  errorDismissBtn.addEventListener("click", hideError);

  let sessionId = null;
  let state = "idle"; // idle | recording | awaiting | playing

  const STATE_LABELS = {
    idle: "Tap the microphone to speak",
    recording: "Listening… tap again when you're done",
    awaiting: "Thinking about a reply…",
    playing: "Playing the reply…",
  };

  const RECORD_ARIA = {
    idle: "Start recording",
    recording: "Stop recording and send",
    awaiting: "Waiting for the reply",
    playing: "Playing the reply",
  };

  function setState(next) {
    state = next;
    statusEl.textContent = STATE_LABELS[next] || next;
    statusEl.dataset.state = next;
    // The button holds icon elements, so drive its look from data-state
    // rather than overwriting its contents with text.
    recordBtn.dataset.state = next;
    recordBtn.setAttribute("aria-label", RECORD_ARIA[next] || next);
    recordBtn.disabled = next === "awaiting" || next === "playing";
  }

  async function startSession({ scenarioId, scenarioTitle, language, languageLabel }) {
    let response;
    try {
      response = await fetch("/api/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId, language }),
      });
    } catch (err) {
      showError("Could not reach the backend to start a session. Is it still running?");
      return;
    }

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      showError(errorBody.detail || `Could not start a session (HTTP ${response.status}).`);
      return;
    }

    const body = await response.json();
    sessionId = body.session_id;

    hideError();
    window.Transcript.clear();

    conversationTitle.textContent = scenarioTitle || scenarioId;
    const tag = document.createElement("span");
    tag.className = "lang-tag";
    tag.textContent = languageLabel || body.language;
    conversationTitle.appendChild(tag);

    scenarioSection.hidden = true;
    conversationSection.hidden = false;
    setState("idle");
  }

  const MIN_RECORDING_BYTES = 2000; // a fraction of a second of real audio is at least this big

  function extensionForMimeType(mimeType) {
    if (mimeType.includes("webm")) return "webm";
    if (mimeType.includes("ogg")) return "ogg";
    if (mimeType.includes("mp4")) return "mp4";
    if (mimeType.includes("wav")) return "wav";
    return "bin";
  }

  // The backend's error `detail` strings are accurate but technical (raw
  // exception text, internal URLs). Map the known per-stage prefixes (see
  // pipeline/turn.py) to non-technical phrasing; fall back to a generic
  // message for anything unrecognized rather than showing the raw detail.
  function friendlyTurnError(detail) {
    if (typeof detail !== "string") return null;
    if (detail.startsWith("speech-to-text failed")) {
      return "Could not understand that recording. Please try again.";
    }
    if (detail.startsWith("language model failed")) {
      return "The AI isn't responding right now. Please try again in a moment.";
    }
    if (detail.startsWith("text-to-speech failed")) {
      return "Got a reply, but could not turn it into speech. Please try again.";
    }
    if (detail.startsWith("no active session") || detail.startsWith("scenario ")) {
      return "This session is no longer valid. Please end it and start a new one.";
    }
    return null;
  }

  async function submitTurn(blob) {
    setState("awaiting");
    const formData = new FormData();
    const extension = extensionForMimeType(blob.type || "");
    formData.append("audio", blob, `turn.${extension}`);

    let response;
    try {
      response = await fetch(`/api/session/${sessionId}/turn`, {
        method: "POST",
        body: formData,
      });
    } catch (err) {
      throw new Error("Could not reach the backend. Check that it's still running and try again.");
    }

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(
        friendlyTurnError(errorBody.detail) || "The AI could not respond. Please try again."
      );
    }

    const body = await response.json();
    window.Transcript.appendTurn(body.user_text, body.ai_text);
    replyAudio.src = `data:audio/wav;base64,${body.audio_base64}`;

    setState("playing");
    hideError();
    try {
      await replyAudio.play();
    } catch (err) {
      // The reply arrived fine; playback itself failing (e.g. blocked by the
      // browser) shouldn't strand the user in "thinking about a reply".
      showError("The reply audio could not play automatically.");
      setState("idle");
    }
  }

  function endSession() {
    // Best-effort cleanup if a recording or playback was in flight, so ending
    // mid-turn doesn't leave a stray mic stream open or the UI looking stuck.
    if (state === "recording") {
      window.Recorder.stop().catch(() => {});
    }
    replyAudio.pause();
    replyAudio.removeAttribute("src");
    replyAudio.load();

    hideError();
    sessionId = null;
    window.Transcript.clear();
    window.ScenarioPicker.reset();
    conversationSection.hidden = true;
    scenarioSection.hidden = false;
    setState("idle");
  }

  endSessionBtn.addEventListener("click", endSession);

  replyAudio.addEventListener("ended", () => {
    setState("idle");
  });

  recordBtn.addEventListener("click", async () => {
    if (state === "idle") {
      hideError();
      try {
        await window.Recorder.start();
        setState("recording");
      } catch (err) {
        showError(err.message);
      }
      return;
    }

    if (state === "recording") {
      try {
        const blob = await window.Recorder.stop();
        if (blob.size < MIN_RECORDING_BYTES) {
          showError(
            "That recording came out empty or too short — check your microphone (browser permission, input device, volume) and try again."
          );
          setState("idle");
          return;
        }
        await submitTurn(blob);
      } catch (err) {
        showError(err.message);
        setState("idle");
      }
    }
  });

  window.ScenarioPicker.init(startSession);
})();
