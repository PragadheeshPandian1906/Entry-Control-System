// ---------- Tab switching ----------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "logs") loadLogs();
  });
});

// ---------- Webcam setup ----------
async function initCamera(videoEl) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoEl.srcObject = stream;
  } catch (err) {
    console.error("Camera access failed:", err);
    alert("Could not access webcam: " + err.message);
  }
}

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
initCamera(video);

const regVideo = document.getElementById("regVideo");
const regCanvas = document.getElementById("regCanvas");
initCamera(regVideo);

function captureFrameAsBlob(videoEl, canvasEl) {
  canvasEl.width = videoEl.videoWidth;
  canvasEl.height = videoEl.videoHeight;
  const ctx = canvasEl.getContext("2d");
  ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);
  return new Promise(resolve => canvasEl.toBlob(resolve, "image/jpeg", 0.92));
}

// ---------- Entry check ----------
document.getElementById("captureBtn").addEventListener("click", async () => {
  const card = document.getElementById("resultCard");
  card.className = "result-card";
  card.innerHTML = `<p class="hint">Processing frame…</p>`;

  const blob = await captureFrameAsBlob(video, canvas);
  const formData = new FormData();
  formData.append("frame_image", blob, "frame.jpg");

  try {
    const resp = await fetch("/api/recognize", { method: "POST", body: formData });
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    renderResult(data);
  } catch (err) {
    card.innerHTML = `<p class="hint">Error: ${err.message}</p>`;
  }
});

function renderResult(data) {
  const card = document.getElementById("resultCard");
  const granted = data.decision === "ACCESS_GRANTED";
  card.className = "result-card " + (granted ? "granted" : "denied");

  card.innerHTML = `
    <div class="decision-banner ${granted ? "granted" : "denied"}">
      ${granted ? "🟢 ACCESS GRANTED" : "🔴 SECURITY VERIFICATION REQUIRED"}
    </div>
    <div class="result-row"><span>Detected Plate</span><span>${data.detected_plate ?? "—"}</span></div>
    <div class="result-row"><span>OCR Confidence</span><span>${(data.ocr_confidence * 100).toFixed(1)}%</span></div>
    <div class="result-row"><span>Plate Match</span><span class="${data.plate_matched ? "check-yes" : "check-no"}">${data.plate_matched ? "✓" : "✗"}</span></div>
    <div class="result-row"><span>Matched Driver</span><span>${data.matched_user_name ?? "—"}</span></div>
    <div class="result-row"><span>Face Detected</span><span>${data.face_detected ? "Yes" : "No"}</span></div>
    <div class="result-row"><span>Face Similarity</span><span>${data.face_similarity !== null ? data.face_similarity.toFixed(3) : "—"}</span></div>
    <div class="result-row"><span>Face Match</span><span class="${data.face_matched ? "check-yes" : "check-no"}">${data.face_matched ? "✓" : "✗"}</span></div>
    <div class="result-row"><span>Reason</span><span>${data.reason}</span></div>
  `;
}

// ---------- Registration ----------
let capturedFaceBlob = null;

document.getElementById("regCaptureBtn").addEventListener("click", async () => {
  capturedFaceBlob = await captureFrameAsBlob(regVideo, regCanvas);
  document.getElementById("regCaptureStatus").innerHTML =
    `<span class="status-ok">Face captured ✓ — ready to register.</span>`;
});

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const statusEl = document.getElementById("registerStatus");

  if (!capturedFaceBlob) {
    statusEl.innerHTML = `<span class="status-err">Please capture a face image first.</span>`;
    return;
  }

  const formData = new FormData();
  formData.append("name", document.getElementById("regName").value);
  formData.append("vehicle_type", document.getElementById("regVehicleType").value);
  formData.append("plate_number", document.getElementById("regPlate").value);
  formData.append("face_image", capturedFaceBlob, "face.jpg");

  statusEl.innerHTML = `<span class="hint">Registering…</span>`;

  try {
    const resp = await fetch("/api/register", { method: "POST", body: formData });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(errText);
    }
    const data = await resp.json();
    statusEl.innerHTML = `<span class="status-ok">Registered "${data.name}" with plate ${data.plate_number} ✓</span>`;
    document.getElementById("registerForm").reset();
    capturedFaceBlob = null;
    document.getElementById("regCaptureStatus").textContent = "";
  } catch (err) {
    statusEl.innerHTML = `<span class="status-err">Failed: ${err.message}</span>`;
  }
});

// ---------- Logs ----------
async function loadLogs() {
  const tbody = document.querySelector("#logsTable tbody");
  tbody.innerHTML = `<tr><td colspan="8">Loading…</td></tr>`;

  const resp = await fetch("/api/logs");
  const logs = await resp.json();

  if (!logs.length) {
    tbody.innerHTML = `<tr><td colspan="8">No entry attempts yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(log => `
    <tr>
      <td>${new Date(log.timestamp).toLocaleString()}</td>
      <td>${log.detected_plate ?? "—"}</td>
      <td>${log.ocr_confidence ? (log.ocr_confidence * 100).toFixed(1) + "%" : "—"}</td>
      <td>${log.matched_user_name ?? "—"}</td>
      <td>${log.face_similarity !== null ? log.face_similarity.toFixed(3) : "—"}</td>
      <td class="${log.plate_matched ? "check-yes" : "check-no"}">${log.plate_matched ? "✓" : "✗"}</td>
      <td class="${log.face_matched ? "check-yes" : "check-no"}">${log.face_matched ? "✓" : "✗"}</td>
      <td>${log.decision === "ACCESS_GRANTED" ? "🟢 GRANTED" : "🔴 VERIFY"}</td>
    </tr>
  `).join("");
}
