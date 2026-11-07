import { loadEnv } from "./env.js";

const toPositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

export function loadConfig(env = loadEnv()) {
  return {
    apiToken: env.RACE_MONITOR_API_TOKEN || env.API_TOKEN || "",
    raceId: env.RACE_MONITOR_RACE_ID || env.RACE_ID || "",
    racerId: env.RACE_MONITOR_RACER_ID || env.RACER_ID || "",
    pollIntervalSeconds: toPositiveInt(env.POLL_INTERVAL_SECONDS, 15),
    port: toPositiveInt(env.PORT, 3000),
    raceMonitorBaseUrl:
      env.RACE_MONITOR_BASE_URL || "https://api.race-monitor.com/v2/Live",
  };
}

export function validateRaceConfig(config) {
  const missing = [];

  if (!config.apiToken) missing.push("RACE_MONITOR_API_TOKEN or API_TOKEN");
  if (!config.raceId) missing.push("RACE_MONITOR_RACE_ID or RACE_ID");
  if (!config.racerId) missing.push("RACE_MONITOR_RACER_ID or RACER_ID");

  return missing;
}
