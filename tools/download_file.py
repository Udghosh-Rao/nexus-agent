import requests, os
from langchain_core.tools import tool

@tool
def download_file(url: str, filename: str) -> str:
    """
    Download a file from a URL and save it to the LLMFiles directory.

    Parameters
    ----------
    url      : str  Direct URL to the file.
    filename : str  Filename to save as (e.g., 'report.pdf').

    Returns
    -------
    str  The saved filename, or an error message.
    """
    try:
        os.makedirs("LLMFiles", exist_ok=True)
        path = os.path.join("LLMFiles", filename)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {filename}")
        return filename
    except Exception as e:
        return f"Error downloading file: {str(e)}"
