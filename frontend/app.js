const totalViolations = document.querySelector("#totalViolations");
const helmetViolations = document.querySelector("#helmetViolations");
const phoneViolations = document.querySelector("#phoneViolations");
const tripleSeatViolations = document.querySelector("#tripleSeatViolations");
const notificationCount = document.querySelector("#notificationCount");
const latestNotificationStatus = document.querySelector("#latestNotificationStatus");
const alertsTable = document.querySelector("#alertsTable");
const refreshButton = document.querySelector("#refreshButton");
const latestViolationImg = document.querySelector("#latestViolationImg");
const latestViolationId = document.querySelector("#latestViolationId");
const latestViolationMeta = document.querySelector("#latestViolationMeta");
const cameraStatus = document.querySelector("#cameraStatus");
const notificationProvider = document.querySelector("#notificationProvider");
const vehicleModelStatus = document.querySelector("#vehicleModelStatus");
const helmetModelStatus = document.querySelector("#helmetModelStatus");
const toastContainer = document.querySelector("#toastContainer");
const startBrowserCamera = document.querySelector("#startBrowserCamera");
const stopBrowserCamera = document.querySelector("#stopBrowserCamera");
const browserCamera = document.querySelector("#browserCamera");
const browserFrameCanvas = document.querySelector("#browserFrameCanvas");
const cameraMessage = document.querySelector("#cameraMessage");
const ownerForm = document.querySelector("#ownerForm");
const plateInput = document.querySelector("#plateInput");
const ownerInput = document.querySelector("#ownerInput");
const phoneInput = document.querySelector("#phoneInput");

let lastSeenViolationId = null;
let browserCameraStream = null;
let browserCameraTimer = null;

async function loadStats() {
  const response = await fetch("/api/stats");
  const stats = await response.json();
  totalViolations.textContent = stats.total ?? 0;
  helmetViolations.textContent = stats.helmet ?? 0;
  phoneViolations.textContent = stats.phone ?? 0;
  tripleSeatViolations.textContent = stats.triple_seat ?? 0;
}

async function loadStatus() {
  const response = await fetch("/api/status");
  const status = await response.json();
  cameraStatus.textContent = formatStatus(status.camera);
  notificationProvider.textContent = formatStatus(status.notifications);
  vehicleModelStatus.textContent = formatStatus(status.vehicle_model);
  helmetModelStatus.textContent = formatStatus(status.helmet_model);
}

function formatStatus(value) {
  if (!value) return "Unknown";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatViolationType(type) {
  switch (type) {
    case "helmet":
      return "Helmet";
    case "phone":
      return "Phone Use";
    case "triple_seat":
      return "Triple Seat";
    default:
      return type.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  }
}

function imageLink(path) {
  if (!path) return "-";
  const href = `/${path.replaceAll("\\", "/")}`;
  return `<a class="image-link" href="${href}" target="_blank" rel="noreferrer">View</a>`;
}

function notificationBadge(status) {
  if (!status) return "-";
  return `<span class="notification-badge ${status}">${formatStatus(status)}</span>`;
}

async function loadViolations() {
  const response = await fetch("/api/violations?limit=20");
  const violations = await response.json();

  if (!violations.length) {
    alertsTable.innerHTML = '<tr><td colspan="6" class="empty">Waiting for live alerts...</td></tr>';
    notificationCount.textContent = "0";
    latestNotificationStatus.textContent = "None yet";
    return [];
  }

  notificationCount.textContent = violations.filter((item) => item.notification_status === "sent").length;
  latestNotificationStatus.textContent = formatStatus(violations[0]?.notification_status || "none yet");

  alertsTable.innerHTML = violations
    .map(
      (item) => `
        <tr>
          <td>${item.violation_id}</td>
          <td>${item.plate_number || item.vehicle_id}</td>
          <td><span class="tag ${item.violation_type}">${formatViolationType(item.violation_type)}</span></td>
          <td>${item.date_time.replace("T", " ")}</td>
          <td>${notificationBadge(item.notification_status)}</td>
          <td>${imageLink(item.image_path)}</td>
        </tr>
      `
    )
    .join("");
  return violations;
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 3600);
}

async function loadLatestViolation() {
  const response = await fetch("/api/violations/latest");
  if (!response.ok) {
    latestViolationImg.removeAttribute("src");
    latestViolationId.textContent = "No violation captured";
    latestViolationMeta.textContent = "Waiting for live detection.";
    return;
  }

  const data = await response.json();
  latestViolationImg.src = `/api/violations/${data.violation_id}/image`;
  latestViolationId.textContent = data.violation_id;
  latestViolationMeta.textContent = `${formatViolationType(data.violation_type)} by vehicle ${data.vehicle_id} at ${data.date_time.replace("T", " ")}`;

  if (data.violation_id !== lastSeenViolationId) {
    if (lastSeenViolationId && data.notification_status === "sent") {
      showToast(`Notification sent for ${data.violation_id}`);
    }
    lastSeenViolationId = data.violation_id;
  }
}

function stopCameraUpload() {
  if (browserCameraTimer) {
    clearInterval(browserCameraTimer);
    browserCameraTimer = null;
  }
  if (browserCameraStream) {
    browserCameraStream.getTracks().forEach((track) => track.stop());
    browserCameraStream = null;
  }
  browserCamera.srcObject = null;
  showToast("Camera stopped");
  showCameraMessage("Browser camera stopped. The backend feed is still available in the processed feed panel.");
}

async function refreshDashboard() {
  try {
    await Promise.all([loadStats(), loadStatus(), loadViolations(), loadLatestViolation()]);
  } catch (error) {
    alertsTable.innerHTML = '<tr><td colspan="6" class="empty">Unable to load live alerts.</td></tr>';
  }
}

refreshButton.addEventListener("click", refreshDashboard);

function showCameraMessage(message) {
  if (cameraMessage) {
    cameraMessage.textContent = message;
  }
}

async function startCameraUpload() {
  if (browserCameraStream) {
    showCameraMessage("Browser camera is already running.");
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showCameraMessage("Browser camera is not supported in this browser.");
    return;
  }

  showCameraMessage("Requesting camera access...");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    browserCameraStream = stream;
    browserCamera.srcObject = stream;
    showToast("Camera connected");
    showCameraMessage("Browser camera connected. Processing frames now.");

    browserCameraTimer = setInterval(async () => {
      if (!browserCamera.videoWidth || !browserCamera.videoHeight) return;
      browserFrameCanvas.width = browserCamera.videoWidth;
      browserFrameCanvas.height = browserCamera.videoHeight;
      const context = browserFrameCanvas.getContext("2d");
      context.drawImage(browserCamera, 0, 0, browserFrameCanvas.width, browserFrameCanvas.height);
      const image = browserFrameCanvas.toDataURL("image/jpeg", 0.72);
      await fetch("/api/browser-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image }),
      });
    }, 450);
  } catch (error) {
    const message = error?.message || "Browser camera access failed.";
    showToast("Browser camera permission failed");
    showCameraMessage(
      `${message} Please allow camera permission in the browser or use the backend processed feed.`
    );
  }
}

startBrowserCamera.addEventListener("click", () => {
  startCameraUpload();
});
stopBrowserCamera.addEventListener("click", stopCameraUpload);

ownerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/api/owners", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      plate_number: plateInput.value,
      owner_name: ownerInput.value,
      phone_number: phoneInput.value,
    }),
  });
  if (response.ok) {
    showToast("Owner saved");
    ownerForm.reset();
  } else {
    showToast("Owner save failed");
  }
});

refreshDashboard();
setInterval(refreshDashboard, 5000);
