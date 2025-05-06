
from logging import LogRecord
from typing import Literal

Reaction = Literal["continue", "retry", "crash", ""]

how_to_react: dict[Reaction, tuple[str, ...]] = {
    "continue": (
        "[Errno 61] Connection refused",
        "Remote end closed connection without response",
        "HTTPError 404: Not Found",
    ),
    "retry": (
        "Unable to download webpage: HTTP Error 522",
        "unable to download video data: HTTP Error 416",
        "HTTPError 500: Internal Server Error",
        "The read operation timed out",
        "Unsupported URL: https://vidmoly.to/",
        "TransportError('timed out')",
        "[Errno 54] Connection reset by peer",
        "HTTPError 503: Service Temporarily Unavailable",
    ),
    "crash": (),
}

def reaction_to(msg: str) -> Reaction:
    for reaction, error_msgs in how_to_react.items():
        for error_msg in error_msgs:
            if error_msg in msg:
                return reaction
    return ""

def is_error_handle(msg: str):
    return bool(reaction_to(msg))

def YDL_log_filter(record: LogRecord):
    if record.filename != "YoutubeDL.py":
        return True

    match record.levelname:
        case "WARNING":
            if any(
                msg in record.msg
                for msg in (
                    "Falling back on generic information extractor",
                    "Live HLS streams are not supported by the native downloader.",
                )
            ):
                return False
            return True
        case "ERROR":
            return not is_error_handle(record.msg)
        case _:
            return True
