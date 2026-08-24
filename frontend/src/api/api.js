// ---------------------------------------------------------------------------
// AgriSetu API client
//
// USE_MOCKS controls whether calls hit local JSON fixtures (public/mock-data)
// or a real backend. On Day 2, flip USE_MOCKS to false and set BASE_URL —
// no other code changes needed since every screen calls through this file.
// ---------------------------------------------------------------------------

export const USE_MOCKS = true;

// Set this to your teammate's backend once it's live, e.g. "https://agrisetu-api.onrender.com"
export const BASE_URL = "http://localhost:8080";

const MOCK_DELAY_MS = 700; // simulates network latency so loading states are visible

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadMock(filename) {
  await delay(MOCK_DELAY_MS);
  const res = await fetch(`/mock-data/${filename}`);
  if (!res.ok) throw new Error(`Mock file ${filename} not found`);
  return res.json();
}

async function realPost(path, body, isMultipart = false) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: isMultipart ? undefined : { "Content-Type": "application/json" },
    body: isMultipart ? body : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Request to ${path} failed: ${res.status}`);
  return res.json();
}

async function realGet(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`Request to ${path} failed: ${res.status}`);
  return res.json();
}

/**
 * POST /api/disease-diagnosis (multipart: image, location, language, device_id)
 * @param {{image: File, location: object, language: string, deviceId?: string}} params
 */
export async function getDiseaseDiagnosis({ image, location, language, deviceId }) {
  if (USE_MOCKS) return loadMock("disease-diagnosis.json");
  const form = new FormData();
  form.append("image", image);
  form.append("location", JSON.stringify(location));
  form.append("language", language);
  
  // Append device_id if provided
  if (deviceId) {
    form.append("device_id", deviceId);
  }
  
  return realPost("/api/disease-diagnosis", form, true);
}


/**
 * POST /api/voice-query (multipart: audio, language)
 * @param {{audio: Blob, language: string}} params
 */
export async function getVoiceQuery({ audio, language }) {
  if (USE_MOCKS) return loadMock("voice-query.json");
  const form = new FormData();
  form.append("audio", audio, "query.webm");
  form.append("language", language);
  return realPost("/api/voice-query", form, true);
}

/**
 * GET /api/cooperation-dashboard
 */
export async function getCooperationDashboard() {
  if (USE_MOCKS) return loadMock("cooperation-dashboard.json");
  return realGet("/api/cooperation-dashboard");
}
