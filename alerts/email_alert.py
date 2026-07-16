import smtplib
from email.mime.text import MIMEText


def send_email(config, subject, html_body, logger=None):
    if not config["alerts"]["email_enabled"]:
        if logger:
            logger.info("Email alert skipped: email_enabled=false")
        return

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = config["alerts"]["email_user"]
    msg["To"] = config["alerts"]["email_to"]

    with smtplib.SMTP(
            config["alerts"]["smtp_server"],
            config["alerts"]["smtp_port"]
    ) as server:
        server.starttls()
        server.login(
            config["alerts"]["email_user"],
            config["alerts"]["email_pass"]
        )
        server.send_message(msg)

    if logger:
        logger.info("Email alert sent to %s", config["alerts"]["email_to"])
