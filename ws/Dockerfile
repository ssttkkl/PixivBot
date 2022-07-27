FROM python:3.10

ENV TZ=Asia/Shanghai

RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime

COPY ./ /app/

WORKDIR /app

# 需要使用清华源的话替换为下面这条语句
# RUN python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && python3 -m pip install -r requirements.txt
RUN python3 -m pip install -r requirements.txt

CMD ["nb", "run"]