from tools import (
    add_dependencies,
    download_file,
    encode_image_to_base64,
    get_rendered_html,
    ocr_image_tool,
    post_request,
    run_code,
    transcribe_audio,
)

GENERAL_TOOLS = [
    run_code,
    get_rendered_html,
    download_file,
    post_request,
    add_dependencies,
    ocr_image_tool,
    transcribe_audio,
    encode_image_to_base64,
]
