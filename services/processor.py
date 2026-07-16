from concurrent.futures import ThreadPoolExecutor, as_completed


def process_chunk(session, config, logger, chunk, worker_func, max_workers, chunk_number=None):
    results = []
    chunk_label = f"chunk {chunk_number}" if chunk_number is not None else "chunk"

    logger.info(
        "Starting %s with %s row(s), max_workers=%s",
        chunk_label,
        len(chunk),
        max_workers
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(worker_func, session, config, logger, row)
            for _, row in chunk.iterrows()
        ]

        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                logger.exception("Unhandled worker failure in %s", chunk_label)
                results.append(["", "", "", "", "", "ERROR", "Unhandled worker failure"])

    success_count = sum(1 for row in results if row[5] == "SUCCESS")
    logger.info(
        "Finished %s: total=%s, success=%s, failed=%s",
        chunk_label,
        len(results),
        success_count,
        len(results) - success_count
    )
    return results
