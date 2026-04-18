import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name = "Autonomous AI Quant Research & Risk Analysis Agent"
    app_version = "3.0.0"

    secret = os.getenv("SECRET", "")
    email = os.getenv("EMAIL", "")

    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    recursion_limit = int(os.getenv("RECURSION_LIMIT", "300"))
    max_tokens = int(os.getenv("MAX_TOKENS", "24000"))


settings = Settings()
