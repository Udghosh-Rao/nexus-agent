FROM python:3.11-slim

WORKDIR /app

RUN pip install uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
