# ======== plugin-build-stage ========
FROM python:3.10 as plugin-build-stage

RUN pip install poetry

# nonebot-plugin-pixivbot

WORKDIR /tmp

RUN git clone https://github.com/ssttkkl/nonebot-plugin-pixivbot.git

WORKDIR /tmp/nonebot-plugin-pixivbot

RUN poetry build

RUN mv /tmp/nonebot-plugin-pixivbot/dist/*.whl /tmp/

# ======== requirements-stage ========
FROM python:3.10-slim as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# ======== image ========
FROM python:3.10-slim

WORKDIR /app

ENV TZ=Asia/Shanghai

RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

COPY ./ /app/

RUN python -m pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY --from=plugin-build-stage /tmp/*.whl /tmp/

RUN python -m pip install --find-links=/tmp nonebot-plugin-pixivbot[mongo]

CMD ["python", "-m", "nb", "run"]
