FROM python:3.9.9

COPY requirements.txt /bot/
COPY src /bot/src
COPY abi /bot/abi
WORKDIR /bot/
RUN python -m pip install -r requirements.txt
RUN python -m pip install markupsafe==2.0.1 --upgrade
