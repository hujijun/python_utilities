FROM python:3.11.1-alpine
WORKDIR /app
COPY ./ /app
RUN pip install -r ./requirements.txt --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
EXPOSE 8000
ENTRYPOINT ["python3","/app/main.py"]
