FROM python:3.10.12
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN pip install python-dotenv
COPY . /bot
CMD python3 discordbot.py