# Repository Guidelines

## Project Structure & Module Organization

RaceMesh displays 24 Hours of Lemons timing data through a Bun service and React dashboard. Active development belongs in `web/`:

- `src/`: React components (`App.jsx`, `Dashboard.jsx`, `LoadingScreen.jsx`) and `styles.css`.
- `server/`: HTTP routes, environment configuration, Race Monitor requests, shared polling cache, and dashboard normalization.
- `scripts/build.js`: frontend bundling and HTML generation; outputs go to ignored `web/dist/`, including `assets/`.
- `LoRA/`: archived Python/Meshtastic/Pygame implementation and an example API response. Preserve it for reference; it is not the active runtime.

## Build, Test, and Development Commands

Run these commands from `web/`:

- `bun install`: install dependencies using `bun.lock`.
- `Copy-Item .env.example .env`: create local configuration in PowerShell; fill in the Race Monitor values.
- `bun run build`: regenerate frontend assets in `dist/`.
- `bun run start`: serve the application at `http://localhost:3000` by default.
- `bun run dev`: restart the server when server files change. Rebuild separately after frontend changes.

## Coding Style & Naming Conventions

Follow existing JavaScript ES modules: two-space indentation, double-quoted strings, semicolons, and trailing commas in multiline structures. Use PascalCase for React components and their filenames, camelCase for functions and variables, and descriptive lowercase CSS classes with hyphens. Keep API fetching and credentials in `server/`; components consume normalized dashboard data. No formatter or linter is currently configured.

## Testing Guidelines

There is no automated test suite, test script, or coverage threshold configured. Validate changes with `bun run build`, then run the service and check `/api/health`, `/api/dashboard`, and the dashboard in a browser. For UI changes, check phone and tablet layouts, loading states, and stale/error indicators. For server changes, verify missing-data handling and cache behavior. If adding automated tests, use Bun's test runner with `*.test.js` files beside the relevant modules and run `bun test` from `web/`.

## Commit & Pull Request Guidelines

History uses short, informal descriptions without a consistent prefix scheme. Write concise, action-oriented subjects, such as `Fix stale dashboard indicator`. Keep changes focused. PRs should describe the behavior changed, list validation performed, link relevant issues, and include screenshots for UI changes.

## Security & Configuration

Never commit `.env` files or API tokens. Configuration precedence is shell environment, `web/.env`, then root `.env`. Keep `.env.example` synchronized with configuration changes and free of secrets.
