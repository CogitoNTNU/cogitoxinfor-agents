FROM python:3.11-slim

# ---------- system deps ----------
RUN apt-get update && apt-get install -y \
        wget xvfb fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 \
        libx11-xcb1 libdrm2 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# ---------- python deps ----------
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---------- Patchright Chrome ----
RUN pip install patchright && patchright install chromium

#
# ---------- REST shim + env ------
# NOTE: Do not commit secrets to version control!
COPY app/server/run_tool.py /srv/run_tool.py
# copy environment file (contains OPENAI_API_KEY, etc.)
COPY .env /srv/.env
WORKDIR /srv
EXPOSE 5000 9222 7900
CMD ["python","run_tool.py"]
# FROM python:3.9-slim

# WORKDIR /app

# # Install system dependencies for Playwright
# RUN apt-get update && apt-get install -y \
#     wget \
#     gnupg \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements first for better caching
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Install Playwright browsers
# RUN playwright install-deps
# RUN playwright install chromium

# # Copy application code
# COPY app ./app

# # Command to run the application
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]