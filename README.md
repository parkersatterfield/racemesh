# RaceMesh

RaceMesh is a race-day web dashboard for 24 Hours of Lemons timing data. The current app runs as a Bun service that keeps Race Monitor credentials server-side, fetches live racer/session data, and serves a fullscreen React dashboard for tablets, phones, and crew laptops.

The original LoRa/Pygame implementation has been archived in `LoRA/`.

## Web App

All active development lives in `web/`.

```bash
cd web
bun install
cp .env.example .env
bun run build
bun run start
```

Open `http://localhost:3000`.

For development, rebuild the frontend after UI changes and restart or run the Bun server in watch mode:

```bash
bun run build
bun run dev
```

## Configuration

The Bun server reads configuration from shell environment variables, `web/.env`, or the root `.env`. Values set in the shell override `web/.env`, and `web/.env` overrides the root `.env`.

- `RACE_MONITOR_API_TOKEN`
- `RACE_MONITOR_RACE_ID`
- `RACE_MONITOR_RACER_ID`
- `POLL_INTERVAL_SECONDS`, default `15`
- `PORT`, default `3000`

For local compatibility with the old Python `.env`, `API_TOKEN`, `RACE_ID`, and `RACER_ID` are also accepted as fallbacks. `.env.example` is only a template and is not read by the app.

## API

- `GET /api/dashboard` returns normalized dashboard data for the driver display.
- `GET /api/health` returns service health and cache status.

The API returns display-ready data instead of raw Race Monitor responses, and it caches successful fetches so multiple viewers share one Race Monitor polling cadence.

## Legacy LoRa Archive

`LoRA/` contains the original Python scripts that fetched Race Monitor data, transmitted compact messages over Meshtastic LoRa, and rendered a Pygame dashboard in the car. It is preserved for reference only and is not maintained as the active runtime.
