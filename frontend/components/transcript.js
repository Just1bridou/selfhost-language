(function () {
  const panel = document.getElementById("transcript-panel");

  function clear() {
    panel.innerHTML = "";
  }

  function appendEntry(speaker, text) {
    const entry = document.createElement("p");
    entry.className = "transcript-entry";
    entry.dataset.speaker = speaker;

    const label = document.createElement("span");
    label.className = "transcript-speaker";
    label.textContent = speaker === "user" ? "You" : "AI";

    entry.appendChild(label);
    entry.appendChild(document.createTextNode(`: ${text}`));
    panel.appendChild(entry);
  }

  function appendTurn(userText, aiText) {
    appendEntry("user", userText);
    appendEntry("ai", aiText);
    panel.scrollTop = panel.scrollHeight;
  }

  window.Transcript = { clear, appendTurn };
})();
