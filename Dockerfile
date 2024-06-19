FROM python:3.11-slim-buster
  WORKDIR /codewars

  COPY . /codewars
  RUN pip install --no-cache-dir -r requirements.txt

  EXPOSE 5000

  CMD ["python", "src/__init__.py"]
