import { validateRaceConfig } from "./config.js";
import { normalizeDashboardData } from "./normalizer.js";
import { fetchRaceMonitorData } from "./raceMonitor.js";

export function createDashboardCache(config, options = {}) {
  const fetcher = options.fetcher ?? fetchRaceMonitorData;
  const now = options.now ?? (() => new Date());
  const minRefreshMs = config.pollIntervalSeconds * 1000;
  let lastSuccess = null;
  let lastFetchAt = 0;
  let inFlight = null;
  let lastError = null;

  async function refreshIfNeeded(force = false) {
    const missing = validateRaceConfig(config);
    if (missing.length > 0) {
      throw new Error(`Missing configuration: ${missing.join(", ")}`);
    }

    const currentTime = now();
    const cacheAge = currentTime.getTime() - lastFetchAt;

    if (!force && lastSuccess && cacheAge < minRefreshMs) {
      return lastSuccess;
    }

    if (!inFlight) {
      inFlight = fetcher(config)
        .then((rawData) => {
          const normalized = normalizeDashboardData(rawData, config, now());
          lastSuccess = normalized;
          lastFetchAt = now().getTime();
          lastError = null;
          return normalized;
        })
        .catch((error) => {
          lastError = error;
          if (lastSuccess) {
            return {
              ...lastSuccess,
              stale: true,
              error: error.message,
            };
          }
          throw error;
        })
        .finally(() => {
          inFlight = null;
        });
    }

    return inFlight;
  }

  return {
    async getDashboard() {
      return refreshIfNeeded(false);
    },
    async refresh() {
      return refreshIfNeeded(true);
    },
    getHealth() {
      return {
        ok: Boolean(lastSuccess) && !lastError,
        hasData: Boolean(lastSuccess),
        stale: Boolean(lastError),
        updatedAt: lastSuccess?.updatedAt ?? null,
        error: lastError?.message ?? null,
        pollIntervalSeconds: config.pollIntervalSeconds,
      };
    },
  };
}
