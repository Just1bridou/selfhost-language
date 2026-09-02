(function () {
  let mediaRecorder = null;
  let chunks = [];
  let stream = null;

  function isSupported() {
    return !!(navigator.mediaDevices && window.MediaRecorder);
  }

  async function start() {
    if (!isSupported()) {
      throw new Error("MediaRecorder is not supported in this browser");
    }
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
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
