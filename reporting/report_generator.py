import os
from datetime import datetime

import pandas as pd


OUTPUT_DIR = "output"


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

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    excel_file = os.path.join(OUTPUT_DIR, f"report_{timestamp}.xlsx")
    html_file = os.path.join(OUTPUT_DIR, f"report_{timestamp}.html")

    df.to_excel(excel_file, index=False)
    df.to_html(html_file, index=False)

    if logger:
        logger.info("Reports generated: excel=%s, html=%s", excel_file, html_file)

    return df, excel_file, html_file
