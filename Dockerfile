FROM python:3.11-slim

# 安装 Chromium 依赖 (DrissionPage 需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    fonts-noto-cjk fonts-wqy-zenhei \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    libxss1 libxtst6 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 数据目录
RUN mkdir -p /app/data

ENV CONFIG_PATH=/app/data/config.json
ENV DISPLAY=:99

# 无头模式入口
CMD ["python", "headless_register.py"]
