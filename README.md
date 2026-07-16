# Nagad User Role Update Script

This project updates Nagad user roles in bulk from an Excel workbook. It logs in through Selenium, copies the authenticated browser cookies into a `requests` session, reads users from `input.xlsx`, fetches each current user record, rebuilds the role payload from the requested role additions/deletions, sends the update API request, and creates Excel/HTML reports for the run.

## What the Script Does

1. Loads settings from `config.yaml`.
2. Opens the Nagad login page with Selenium Chrome and signs in using the configured credentials.
3. Transfers Selenium cookies into a reusable `requests.Session`.
4. Reads `input.xlsx` with pandas.
5. Processes users in chunks using a thread pool.
6. For each `userId`:
   - Fetches the current user data from the configured GET API.
   - Reads `Role Addition` and `Role Deletion` from Excel.
   - Removes role IDs listed in `Role Deletion` from the current role list.
   - Adds or keeps role IDs listed in `Role Addition`.
   - Removes duplicate roles while preserving the final role order.
   - Sends the updated payload to the configured PUT API.
7. Generates timestamped reports with previous roles, new roles, status, result, and message.
8. Sends optional Telegram and email alerts when configured.

## Project Structure

```text
.
|-- main.py                         # Main entry point and per-user worker
|-- config.yaml                     # Environment, credentials, processing, and alert settings
|-- input.xlsx                      # Input user list
|-- core/
|   |-- config_loader.py            # YAML config loader
|   |-- logger.py                   # File and console logger setup
|   `-- session_manager.py          # Selenium login, cookie session, auto-refresh
|-- services/
|   |-- processor.py                # Chunk/thread processing
|   `-- user_service.py             # Fetch, payload build, and update API calls
|-- reporting/
|   `-- report_generator.py         # Excel and HTML report generation
|-- alerts/
|   |-- telegram.py                 # Telegram summary notification
|   `-- email_alert.py              # Email report notification
`-- logs/                           # Timestamped run logs
```

## Input File Format

`input.xlsx` must contain these columns:

| Column | Purpose |
| --- | --- |
| `userId` | User ID to fetch and update |
| `Role Addition` | Role IDs to add/keep for the user |
| `Role Deletion` | Role IDs to remove from the user |

Role ID cells can contain a single ID or multiple IDs separated by commas, spaces, semicolons, pipes, or new lines.

Examples:

```text
12
12,81100
12; 81100
12 81100
```

Blank cells are treated as no change for that column.

## Role Rules

The current role logic is in `services/user_service.py`.

| Rule | Behavior |
| --- | --- |
| Existing roles | Preserved unless listed in `Role Deletion` |
| `Role Deletion` | Removes listed role IDs from the current role list |
| `Role Addition` | Adds listed role IDs if they are missing |
| Duplicate roles | Removed while building the new role list |
| Same ID in both columns | `Role Addition` wins, so the role remains in the final payload |

## Configuration

Copy `config.example.yaml` to `config.yaml`, then edit `config.yaml` before running:

- `environment.login_url`: Selenium login URL.
- `environment.get_user_url`: API used to fetch current user data.
- `environment.update_user_url`: API used to submit the updated user payload.
- `credentials.username` and `credentials.password`: Login credentials.
- `processing.chunk_size`: Number of Excel rows per batch.
- `processing.max_workers`: Number of parallel worker threads.
- `processing.request_timeout`: API timeout in seconds.
- `processing.session_refresh_interval`: How often Selenium refreshes the session cookies.
- `alerts`: Optional Telegram/email notification settings.

`config.yaml` is ignored by Git. Do not commit real credentials, bot tokens, or passwords to source control.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The script also needs Google Chrome and a compatible ChromeDriver available to Selenium. Selenium Manager may download/manage the driver automatically in recent Selenium versions.

## Run

Place the Excel workbook at `input.xlsx`, then run:

```bash
python main.py
```

The script will print a short summary at the end.

## Output

Each run creates:

- `logs/run_YYYYMMDD_HHMMSS.log`
- `report_YYYYMMDD_HHMMSS.xlsx`
- `report_YYYYMMDD_HHMMSS.html`

The report columns are:

| Column | Description |
| --- | --- |
| `userId` | Processed user ID |
| `PreviousRoles` | Roles before update |
| `NewRoles` | Roles sent in the update payload |
| `PreviousStatus` | Status before update |
| `NewStatus` | Status sent in the update payload |
| `Result` | `SUCCESS`, `FAILED`, or `ERROR` |
| `Message` | API response or error detail |

## Logging

Logs are written to `logs/` and also displayed in the console. A normal run records:

- Log file creation.
- Job startup.
- Selenium login and cookie transfer.
- Session auto-refresh startup.
- Input workbook row count.
- Processing settings.
- Chunk start and finish totals.
- Per-user processing start.
- Role IDs requested for addition and deletion.
- User-not-found cases.
- Previous and new role IDs for each update.
- Update success or failed API response.
- Report file names.
- Telegram/email alert status.
- Final run summary.

Exceptions are logged with stack traces using `logger.exception`, which makes troubleshooting easier without changing the final report format.

## Safety Notes

- The script sends real update requests to the configured `update_user_url`.
- Test with a small input file before running a large batch.
- Keep `max_workers` conservative if the target API has rate limits.
- The script disables HTTPS certificate warnings because API calls use `verify=False`; only use this in trusted internal environments.
