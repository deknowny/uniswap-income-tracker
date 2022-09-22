FROM python:3.9.9

COPY requirements.txt abi.json erc20.json users.json factory.json pool.json /bot/
COPY src /bot/src
WORKDIR /bot/
RUN python -m pip install -r requirements.txt
RUN python -m pip install markupsafe==2.0.1 --upgrade

