"""Things that only make sense when the app runs on your own computer (debug mode, the browser on
the same machine): show a saved cut-out in the file manager (wish Olaf, 8-11-2026). On a server,
such as Toolforge, nobody can see its disk; there the app offers Open file and Download instead."""

import subprocess
import sys
from pathlib import Path


def show_in_folder(path: Path) -> None:
    """Open the file manager at the folder of `path`, with the file selected where the system
    can. No shell: the path goes to the program as one argument."""
    path = Path(path).resolve()
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", f"/select,{path}"])  # noqa: S603, S607 (fixed program, no shell)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)])  # noqa: S603, S607
    else:
        subprocess.Popen(["xdg-open", str(path.parent)])  # noqa: S603, S607
