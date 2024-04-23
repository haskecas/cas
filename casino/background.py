from flask import Flask, request
from threading import Thread
import time
import requests

app = Flask(__name__)


@app.route('/')
def home():
  return "I'm alive"


def run():
  app.run(host='0.0.0.0', port=80)


def keep_alive():
  print("keep alive called")
  t = Thread(target=run)
  t.start()
