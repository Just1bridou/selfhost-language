(function () {
  const scenarioSection = document.getElementById("scenario-picker");
  const conversationSection = document.getElementById("conversation");
  const conversationTitle = document.getElementById("conversation-title");
  const statusEl = document.getElementById("status-indicator");
  const recordBtn = document.getElementById("record-btn");
  const replyAudio = document.getElementById("reply-audio");
  const transcriptPanel = document.getElementById("transcript-panel");

  // Created here rather than in index.html: #conversation is already only
  // ever visible while a session is active, so inserting this button as one
  // of its children satisfies "visible whenever a session is active" (AC#1)
  // with no extra show/hide logic of its own.
  const endSessionBtn = document.createElement("button");
  endSessionBtn.id = "end-session-btn";
  endSessionBtn.type = "button";
  endSessionBtn.textContent = "End session";
  endSessionBtn.style.marginTop = "1rem";
  conversationSection.insertBefore(endSessionBtn, transcriptPanel);

  let sessionId = null;
  let state = "idle"; // idle | recording | awaiting | playing

  const STATE_LABELS = {
    idle: "Idle — press Record to speak",
    recording: "Recording… press Stop to send",
    awaiting: "Waiting for the AI's reply…",
    playing: "Playing the AI's reply…",
  };

  function setState(next) {
    state = next;
    statusEl.textContent = STATE_LABELS[next] || next;
    statusEl.dataset.state = next;
    recordBtn.textContent = next === "recording" ? "Stop" : "Record";
    recordBtn.disabled = next === "awaiting" || next === "playing";
  }

  async function startSession(scenarioId) {
    const response = await fetch("/api/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    });
    if (!response.ok) {
      throw new Error(`failed to start session: HTTP ${response.status}`);
    }
    const body = await response.json();
    sessionId = body.session_id;

    window.Transcript.clear();
    scenarioSection.hidden = true;
    conversationSection.hidden = false;
    conversationTitle.textContent = `Scenario: ${scenarioId}`;
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

  async function submitTurn(blob) {
    setState("awaiting");
    const formData = new FormData();
    const extension = extensionForMimeType(blob.type || "");
    formData.append("audio", blob, `turn.${extension}`);

    const response = await fetch(`/api/session/${sessionId}/turn`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `turn failed: HTTP ${response.status}`);
    }

    const body = await response.json();
    window.Transcript.appendTurn(body.user_text, body.ai_text);
    replyAudio.src = `data:audio/wav;base64,${body.audio_base64}`;

    setState("playing");
    await replyAudio.play();
  }

  function endSession() {
    // Best-effort cleanup if a recording or playback was in flight, so
    // ending mid-turn doesn't leave a stray mic stream open or the UI in a
    // state that looks stuck (edge case from Testing).
    if (state === "recording") {
      window.Recorder.stop().catch(() => {});
    }
    replyAudio.pause();
    replyAudio.removeAttribute("src");
    replyAudio.load();

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
      try {
        await window.Recorder.start();
        setState("recording");
      } catch (err) {
        statusEl.textContent = `Could not start recording: ${err.message}`;
      }
      return;
    }

    if (state === "recording") {
      try {
        const blob = await window.Recorder.stop();
        if (blob.size < MIN_RECORDING_BYTES) {
          statusEl.textContent =
            "That recording came out empty or too short — check your microphone (browser permission, input device, volume) and try again.";
          setState("idle");
          return;
        }
        await submitTurn(blob);
      } catch (err) {
        statusEl.textContent = `Turn failed: ${err.message}`;
        setState("idle");
      }
    }
  });

  window.ScenarioPicker.init(startSession);
})();
