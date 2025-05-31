FROM python:3.11-slim
WORKDIR /app
COPY src src
CMD ["python","-c","print('phoenix_trader container OK')"]
