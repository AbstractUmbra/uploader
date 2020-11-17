FROM python:3.9.0-buster

WORKDIR /usr/src/app

COPY python/* ./
RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
