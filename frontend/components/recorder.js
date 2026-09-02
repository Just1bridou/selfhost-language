(function () {
  const PREFERRED_MIME_TYPES = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/mp4",
  ];

  let mediaRecorder = null;
  let chunks = [];
  let stream = null;

  function isSupported() {
    return !!(navigator.mediaDevices && window.MediaRecorder);
  }

  function pickMimeType() {
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) {
      return "";
    }
    return PREFERRED_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  }

  async function start() {
    if (!isSupported()) {
      throw new Error("Voice recording is not supported in this browser.");
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "SecurityError") {
        throw new Error(
          "Microphone access was denied. Allow microphone access for this page in your browser's site settings, then try again."
        );
      }
      if (err.name === "NotFoundError") {
        throw new Error("No microphone was found. Connect a microphone and try again.");
      }
      throw new Error(`Could not access the microphone: ${err.message}`);
    }

    chunks = [];

    // Explicitly pick a supported mimeType rather than relying on the
    // browser's default: different browsers (Safari especially) default to
    // different containers, and leaving it unset has been observed to
    // produce audio the backend struggles to decode correctly.
    const mimeType = pickMimeType();
    mediaRecorder = mimeType
      ? new MediaRecorder(stream, { mimeType })
      : new MediaRecorder(stream);

    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size > 0) {
        chunks.push(event.data);
      }
    });
    mediaRecorder.start();
  }

  function stop() {
    return new Promise((resolve, reject) => {
      if (!mediaRecorder) {
        reject(new Error("recording was not started"));
        return;
      }
      mediaRecorder.addEventListener(
        "stop",
        () => {
          const blob = new Blob(chunks, {
            type: mediaRecorder.mimeType || "audio/webm",
          });
          stream.getTracks().forEach((track) => track.stop());
          resolve(blob);
        },
        { once: true }
      );
      mediaRecorder.stop();
    });
  }

  window.Recorder = { isSupported, start, stop };
})();
