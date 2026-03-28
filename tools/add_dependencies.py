import subprocess
from typing import List
from langchain_core.tools import tool

@tool
def add_dependencies(dependencies: List[str]) -> str:
    """
    Install Python packages at runtime using uv.

    Parameters
    ----------
    dependencies : List[str]
        List of PyPI package names to install (e.g., ['numpy', 'pandas']).

    Returns
    -------
    str  Success or failure message.
    """
    try:
        subprocess.check_call(
            ["uv", "add"] + dependencies,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return f"Successfully installed: {', '.join(dependencies)}"
    except subprocess.CalledProcessError as e:
        return f"Installation failed (exit {e.returncode}): {e.stderr or 'No error output.'}"
    except Exception as e:
        return f"Unexpected error: {e}"
