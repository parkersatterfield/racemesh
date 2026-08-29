function valueOrDash(value) {
  return value || "-";
}

function CompetitorLine({ label, competitor, emptyLabel, tone }) {
  if (!competitor) {
    return (
      <div className="gap-line">
        <span>{label}</span>
        <strong>{emptyLabel}</strong>
      </div>
    );
  }

  return (
    <div className="gap-line">
      <span>{label}</span>
      <strong>
        #{valueOrDash(competitor.number)} {valueOrDash(competitor.name)}
      </strong>
      <em className={tone}>{valueOrDash(competitor.totalTime)}</em>
    </div>
  );
}

export function Dashboard({ data, ageSeconds, error }) {
  const competitor = data.competitor || {};
  const stale = data.stale || Boolean(error) || (ageSeconds ?? 0) > 120;

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <strong>RaceMesh</strong>
          <span>{valueOrDash(data.session?.trackName)}</span>
        </div>
        <div className={stale ? "signal stale" : "signal"}>
          <span />
          {stale ? "Stale" : valueOrDash(data.session?.flagStatus)}
        </div>
      </header>

      <section className="hero-row" aria-label="Current race position">
        <div>
          <p className="eyebrow">Position</p>
          <h1>P{valueOrDash(competitor.position)}</h1>
          <p className="muted">
            Best P{valueOrDash(competitor.bestPosition)} - Class{" "}
            {valueOrDash(data.classPosition)}/{valueOrDash(data.totalInClass)}
          </p>
        </div>
        <div className="time-block">
          <p className="eyebrow">Elapsed</p>
          <strong>{valueOrDash(competitor.totalTime)}</strong>
          <span>Car #{valueOrDash(competitor.number)}</span>
        </div>
      </section>

      <section className="race-strip" aria-label="Session details">
        <div>
          <span>Session</span>
          <strong>{valueOrDash(data.session?.name)}</strong>
        </div>
        <div>
          <span>Time To Go</span>
          <strong>{valueOrDash(data.session?.timeToGo)}</strong>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <p className="eyebrow">Laps</p>
          <div className="fastest">
            <span>Fastest</span>
            <strong>{valueOrDash(competitor.bestLapTime)}</strong>
            <em>L{valueOrDash(competitor.bestLap)}</em>
          </div>
          <div className="lap-list">
            {data.recentLaps?.length ? (
              data.recentLaps.map((lap) => (
                <div
                  className={lap.lap === competitor.bestLap ? "lap best" : "lap"}
                  key={lap.lap}
                >
                  <span>L{valueOrDash(lap.lap)}</span>
                  <strong>{valueOrDash(lap.lapTime)}</strong>
                </div>
              ))
            ) : (
              <div className="empty">Waiting for lap data</div>
            )}
          </div>
        </div>

        <div className="panel">
          <p className="eyebrow">Class Traffic</p>
          <div className="gap-list">
            <CompetitorLine
              label="Ahead"
              competitor={data.carAhead}
              emptyLabel="Leading"
              tone="gain"
            />
            <CompetitorLine
              label="Behind"
              competitor={data.carBehind}
              emptyLabel="Last in class"
              tone="loss"
            />
          </div>
        </div>
      </section>

      <footer className={stale ? "status stale" : "status"}>
        <span>{stale ? "Data stale" : "Live data"}</span>
        <strong>
          {ageSeconds === null ? "Waiting for update" : `Updated ${ageSeconds}s ago`}
        </strong>
        {error ? <em>{error}</em> : null}
      </footer>
    </main>
  );
}
