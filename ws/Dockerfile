FROM python:3.10

ENV TZ=Asia/Shanghai

RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone

COPY ./ /app/

WORKDIR /app

RUN python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && python3 -m pip install -r requirements.txt
RUN python3 -m pip install dist/*.whl

CMD ["nb", "run"]
