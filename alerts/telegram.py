import requests


def send_telegram(config, message, logger=None):
    token = config["alerts"]["telegram_bot_token"]
    chat_id = config["alerts"]["telegram_chat_id"]

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        if logger:
            logger.info("Telegram alert skipped: bot token is not configured")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=30)
    if logger:
        logger.info("Telegram alert response status=%s", response.status_code)
    response.raise_for_status()
