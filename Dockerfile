FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

ENV APP_MODULE=bot:app
ENV MAX_WORKERS=1

ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY ./ /app/

WORKDIR /app

RUN python3 -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && python3 -m pip install -r requirements.txt
