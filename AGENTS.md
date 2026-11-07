# Repository Guidelines

## Project Structure & Module Organization

RaceMesh sends Race-Monitor telemetry over Meshtastic LoRa to an in-car Pygame dashboard. Python modules live at the repository root:

- `sender.py`: fetches racer/session data and transmits telemetry.
- `receiver.py`: parses messages and renders the 800×480 dashboard.
- `dto.py`: Pydantic models for API responses.
- `constants.py`: serial ports, node IDs, race IDs, and API endpoints.
- `lora.py`: standalone radio smoke test.
- `example_response.json`: sample racer response for manual testing.

`pyproject.toml` defines dependencies; `uv.lock` pins their resolved versions. There is no tracked frontend, dedicated asset directory, or test suite.

## Build, Test, and Development Commands

Use Python 3.12 and run commands from the repository root:

- `uv sync`: install dependencies into the local virtual environment.
- `uv run sender.py`: start API polling and LoRa transmission; requires a configured radio and API token.
- `uv run receiver.py`: start the dashboard and radio listener. Display initialization currently forces Linux KMS/DRM settings; review these when developing on another platform.
- `uv run lora.py`: send a test message to the configured receiver node.
- `uv run python -m compileall constants.py dto.py sender.py receiver.py lora.py`: check Python syntax without starting the application.

No separate build command is configured.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, `PascalCase` classes, and uppercase constants. Preserve API field names such as `RacerID` in DTOs. Follow existing formatting; no formatter or linter is configured. Coordinate sender and receiver changes to pipe-delimited messages such as `POS|position|best_position`.

## Testing Guidelines

No automated framework or coverage threshold is configured. Use `example_response.json` and `mock_fetch_race_data()` for manual checks; the helper replaces only racer fetching, while sender startup still opens serial hardware and session fetching remains live. Validate protocol changes on both nodes, including malformed messages and missing competitors. Check display changes at 800×480 and capture screenshots.

## Commit & Pull Request Guidelines

History uses short, informal action summaries such as `improve rendering`; no strict commit prefix is established. Prefer specific, imperative subjects. PRs should explain behavior changes, link relevant issues, record validation and hardware used, and include screenshots for dashboard changes.

## Security & Configuration

Keep `API_TOKEN` in the ignored `.env` file. Configure ports and IDs in `constants.py`; `lora.py` also has its own port setting. Never commit credentials or share unredacted sender logs: startup currently prints a URL containing the API token.
