const emptyValue = "-";

function asString(value, fallback = emptyValue) {
  if (value === undefined || value === null || value === "") return fallback;
  return String(value);
}

function numericPosition(competitor) {
  const parsed = Number.parseInt(competitor?.Position ?? "", 10);
  return Number.isFinite(parsed) ? parsed : Number.MAX_SAFE_INTEGER;
}

function formatName(competitor) {
  const first = asString(competitor?.FirstName, "").trim();
  const last = asString(competitor?.LastName, "").trim();
  return `${first} ${last}`.trim() || emptyValue;
}

function normalizeCompetitor(competitor) {
  if (!competitor) return null;

  return {
    racerId: asString(competitor.RacerID),
    number: asString(competitor.Number),
    name: formatName(competitor),
    firstName: asString(competitor.FirstName, ""),
    lastName: asString(competitor.LastName, ""),
    classId: asString(competitor.ClassID),
    position: asString(competitor.Position),
    laps: asString(competitor.Laps),
    totalTime: asString(competitor.TotalTime),
    bestPosition: asString(competitor.BestPosition),
    bestLap: asString(competitor.BestLap),
    bestLapTime: asString(competitor.BestLapTime),
    lastLapTime: asString(competitor.LastLapTime),
  };
}

function normalizeLaps(laps = []) {
  return [...laps]
    .sort(
      (a, b) =>
        Number.parseInt(a.Lap ?? "0", 10) -
        Number.parseInt(b.Lap ?? "0", 10),
    )
    .map((lap) => ({
      lap: asString(lap.Lap),
      position: asString(lap.Position),
      lapTime: asString(lap.LapTime),
      flagStatus: asString(lap.FlagStatus),
      totalTime: asString(lap.TotalTime),
    }));
}

function findSessionCompetitor(competitors, racerId, fallbackCompetitor) {
  const expected = String(racerId);

  return (
    competitors.find(
      (competitor) =>
        String(competitor.RacerID) === expected ||
        String(competitor.Number).replace(/^#/, "") === expected ||
        String(competitor.Transponder) === expected,
    ) || fallbackCompetitor
  );
}

function findClassNeighbors(competitors, myCompetitor) {
  if (!myCompetitor) {
    return {
      carAhead: null,
      carBehind: null,
      classPosition: emptyValue,
      totalInClass: 0,
    };
  }

  const classCompetitors = competitors
    .filter(
      (competitor) =>
        competitor.ClassID === myCompetitor.ClassID && competitor.Position,
    )
    .sort((a, b) => numericPosition(a) - numericPosition(b));

  const myIndex = classCompetitors.findIndex(
    (competitor) => competitor.RacerID === myCompetitor.RacerID,
  );

  return {
    carAhead: myIndex > 0 ? normalizeCompetitor(classCompetitors[myIndex - 1]) : null,
    carBehind:
      myIndex >= 0 && myIndex < classCompetitors.length - 1
        ? normalizeCompetitor(classCompetitors[myIndex + 1])
        : null,
    classPosition: asString(myCompetitor.Position),
    totalInClass: classCompetitors.length,
  };
}

export function normalizeDashboardData(
  { racerResponse, sessionResponse },
  config,
  now = new Date(),
) {
  const racerCompetitor = racerResponse?.Details?.Competitor;
  const competitors = Object.values(sessionResponse?.Session?.Competitors ?? {});
  const mySessionCompetitor = findSessionCompetitor(
    competitors,
    config.racerId,
    racerCompetitor,
  );
  const neighbors = findClassNeighbors(competitors, mySessionCompetitor);
  const laps = normalizeLaps(racerResponse?.Details?.Laps ?? []);
  const competitor = normalizeCompetitor(racerCompetitor);

  return {
    updatedAt: now.toISOString(),
    stale: false,
    pollIntervalSeconds: config.pollIntervalSeconds,
    session: {
      name: asString(sessionResponse?.Session?.SessionName),
      trackName: asString(sessionResponse?.Session?.TrackName),
      flagStatus: asString(sessionResponse?.Session?.FlagStatus),
      timeToGo: asString(sessionResponse?.Session?.TimeToGo),
    },
    competitor,
    classPosition: neighbors.classPosition,
    totalInClass: neighbors.totalInClass,
    laps,
    recentLaps: laps.slice(-3).reverse(),
    carAhead: neighbors.carAhead,
    carBehind: neighbors.carBehind,
  };
}
