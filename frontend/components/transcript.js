(function () {
  const panel = document.getElementById("transcript-panel");

  function renderEmptyState() {
    panel.innerHTML = "";
    const empty = document.createElement("p");
    empty.className = "transcript-empty";
    empty.textContent = "Your conversation will appear here.";
    panel.appendChild(empty);
  }

  function clear() {
    renderEmptyState();
  }

  function appendEntry(speaker, text) {
    const empty = panel.querySelector(".transcript-empty");
    if (empty) {
      empty.remove();
    }

    const msg = document.createElement("div");
    msg.className = "msg";
    msg.dataset.speaker = speaker;

    const role = document.createElement("span");
    role.className = "msg-role";
    role.textContent = speaker === "user" ? "You" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.textContent = text;

    msg.appendChild(role);
    msg.appendChild(bubble);
    panel.appendChild(msg);
  }

  function appendTurn(userText, aiText) {
    appendEntry("user", userText);
    appendEntry("ai", aiText);
    panel.scrollTop = panel.scrollHeight;
  }

  renderEmptyState();

  window.Transcript = { clear, appendTurn };
})();
