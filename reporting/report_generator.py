import pandas as pd
from datetime import datetime


def generate_reports(results, logger=None):
    columns = [
        "userId",
        "PreviousRoles",
        "NewRoles",
        "PreviousStatus",
        "NewStatus",
        "Result",
        "Message"
    ]

    df = pd.DataFrame(results, columns=columns)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    excel_file = f"report_{timestamp}.xlsx"
    html_file = f"report_{timestamp}.html"

    df.to_excel(excel_file, index=False)
    df.to_html(html_file, index=False)

    if logger:
        logger.info("Reports generated: excel=%s, html=%s", excel_file, html_file)

    return df, excel_file, html_file
