import os

import uvicorn


def get_port() -> int:
    port = os.getenv("PORT", "8000")

    try:
        return int(port)
    except ValueError as exc:
        raise RuntimeError(f"PORT must be an integer, got {port!r}.") from exc


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=get_port(),
    )