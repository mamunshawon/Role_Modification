import time


def retry(func, attempts=3):
    def wrapper(*args, **kwargs):
        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)
            except Exception:
                time.sleep(2 ** attempt)
        raise Exception("Max retry exceeded")

    return wrapper
