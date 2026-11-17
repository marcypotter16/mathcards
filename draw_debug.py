"""Short-lived console trace for investigating card draws."""

from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().with_name("draw_debug.log")
_frame = 0
_trace_until_frame = -1

# Start each application run with a clean log so it always contains the latest capture.
LOG_PATH.write_text(
    f"=== Draw debug run started {datetime.now().astimezone().isoformat(timespec='seconds')} ===\n",
    encoding="utf-8",
)


def begin_frame() -> None:
    global _frame
    _frame += 1


def arm_draw_trace(frame_count: int = 8) -> None:
    global _trace_until_frame
    _trace_until_frame = _frame + frame_count
    _write_line(f"[DRAWDBG frame={_frame}] trace armed for {frame_count + 1} frames")


def draw_debug(*parts: object) -> None:
    if _frame <= _trace_until_frame:
        _write_line(f"[DRAWDBG frame={_frame}] {' '.join(map(str, parts))}")


def _write_line(line: str) -> None:
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")
        log_file.flush()
