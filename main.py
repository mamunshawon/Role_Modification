import pandas as pd
from core.config_loader import load_config
from core.logger import setup_logger
from core.session_manager import SessionManager
from services.user_service import fetch_user, build_payload, update_user, parse_role_ids
from services.processor import process_chunk
from reporting.report_generator import generate_reports
from alerts.telegram import send_telegram
from alerts.email_alert import send_email
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def worker(session, config, logger, row):
    user_id = str(row["userId"]).strip()

    role_addition_value = row.get("Role Addition", "")
    role_deletion_value = row.get("Role Deletion", "")

    try:
        role_additions = parse_role_ids(role_addition_value)
        role_deletions = parse_role_ids(role_deletion_value)

        logger.info(
            "Processing userId=%s, role_additions=%s, role_deletions=%s",
            user_id,
            role_additions,
            role_deletions
        )
        user = fetch_user(session, config, user_id)

        if not user:
            logger.warning("User not found: userId=%s", user_id)
            return [
                user_id,
                "",
                "",
                "",
                "",
                "FAILED",
                "User not found"
            ]

        # ===== Previous Data =====
        previous_roles = ",".join(
            str(r["id"]) for r in user.get("roleList", [])
        )

        previous_status = user.get("status", "")

        # ===== Build Payload =====
        payload = build_payload(user, role_addition_value, role_deletion_value)

        new_roles = ",".join(
            str(r["id"]) for r in payload.get("roleList", [])
        )

        new_status = payload.get("status", "")

        # ===== Update =====
        logger.info(
            "Updating userId=%s, added_roles=%s, deleted_roles=%s, previous_roles=%s, new_roles=%s, previous_status=%s, new_status=%s",
            user_id,
            role_additions,
            role_deletions,
            previous_roles,
            new_roles,
            previous_status,
            new_status
        )
        response = update_user(session, config, payload)

        if response.status_code == 200:
            result = "SUCCESS"
            message = "Updated"
            logger.info("Update successful for userId=%s", user_id)
        else:
            result = "FAILED"
            message = response.text
            logger.error(
                "Update failed for userId=%s, status=%s, response=%s",
                user_id,
                response.status_code,
                response.text
            )

        return [
            user_id,
            previous_roles,
            new_roles,
            previous_status,
            new_status,
            result,
            message
        ]

    except Exception as e:
        logger.exception("Error while processing userId=%s", user_id)
        return [
            user_id,
            "",
            "",
            "",
            "",
            "ERROR",
            str(e)
        ]


def main():
    config = load_config()
    logger = setup_logger()
    logger.info("Starting Nagad user update job")
    session = SessionManager(config, logger)

    logger.info("Reading input workbook: input.xlsx")
    df = pd.read_excel("input.xlsx")
    required_columns = {"userId", "Role Addition", "Role Deletion"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"input.xlsx is missing required column(s): {sorted(missing_columns)}")
    logger.info("Loaded %s row(s) from input workbook", len(df))

    chunk_size = config["processing"]["chunk_size"]
    max_workers = config["processing"]["max_workers"]
    logger.info("Processing settings: chunk_size=%s, max_workers=%s", chunk_size, max_workers)

    results = []

    for chunk_number, start in enumerate(range(0, len(df), chunk_size), start=1):
        chunk = df.iloc[start:start + chunk_size]
        results.extend(
            process_chunk(session, config, logger, chunk, worker, max_workers, chunk_number)
        )

    logger.info("All chunks processed. Generating reports.")
    df_report, excel_file, html_file = generate_reports(results, logger)

    summary = f"""
    Total: {len(df_report)}
    Success: {(df_report['Result'] == 'SUCCESS').sum()}
    Failed: {(df_report['Result'] != 'SUCCESS').sum()}
    """

    logger.info("Run summary:%s", summary)

    try:
        send_telegram(config, summary, logger)
    except Exception:
        logger.exception("Telegram alert failed")

    try:
        send_email(config, "Nagad User Update Report", df_report.to_html(), logger)
    except Exception:
        logger.exception("Email alert failed")

    print(summary)
    logger.info("Job completed. excel_report=%s, html_report=%s", excel_file, html_file)


if __name__ == "__main__":
    main()
