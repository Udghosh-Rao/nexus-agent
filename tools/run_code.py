import subprocess, os
from langchain_core.tools import tool

OUTPUT_LIMIT = 10_000

@tool
def run_code(code: str) -> dict:
    """
    Execute Python code in a sandboxed subprocess and return its output.

    Parameters
    ----------
    code : str
        Valid Python source code to execute.

    Returns
    -------
    dict
        {
            "stdout":      "<program output>",
            "stderr":      "<errors if any>",
            "return_code": 0
        }
    """
    try:
        os.makedirs("LLMFiles", exist_ok=True)
        filepath = os.path.join("LLMFiles", "runner.py")

        with open(filepath, "w") as f:
            f.write(code)

        proc = subprocess.Popen(
            ["uv", "run", "runner.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="LLMFiles"
        )
        stdout, stderr = proc.communicate()

        if len(stdout) > OUTPUT_LIMIT:
            stdout = stdout[:OUTPUT_LIMIT] + "\n... [TRUNCATED]"
        if len(stderr) > OUTPUT_LIMIT:
            stderr = stderr[:OUTPUT_LIMIT] + "\n... [TRUNCATED]"

        return {"stdout": stdout, "stderr": stderr, "return_code": proc.returncode}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "return_code": -1}
