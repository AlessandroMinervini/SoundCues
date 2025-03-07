FROM python:3.10-alpine

WORKDIR /api
COPY requirements.txt .

RUN pip install -r requirements.txt
COPY . .
EXPOSE 7860

CMD ["sh", "-c", "export HF_HOME=/tmp && python app.py"]
