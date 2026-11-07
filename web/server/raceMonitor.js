function buildUrl(config, path, params) {
  const url = new URL(`${config.raceMonitorBaseUrl}/${path}`);

  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  url.searchParams.set("apiToken", config.apiToken);
  return url;
}

async function postJson(url) {
  const response = await fetch(url, { method: "POST" });

  if (!response.ok) {
    throw new Error(`Race Monitor returned ${response.status}`);
  }

  return response.json();
}

export async function fetchRaceMonitorData(config) {
  const racerUrl = buildUrl(config, "GetRacer", {
    racerId: config.racerId,
    raceId: config.raceId,
  });
  const sessionUrl = buildUrl(config, "GetSession", {
    raceId: config.raceId,
  });

  const [racerResponse, sessionResponse] = await Promise.all([
    postJson(racerUrl),
    postJson(sessionUrl),
  ]);

  if (!racerResponse.Successful) {
    throw new Error("Race Monitor racer response was not successful");
  }

  if (!sessionResponse.Successful) {
    throw new Error("Race Monitor session response was not successful");
  }

  return { racerResponse, sessionResponse };
}
