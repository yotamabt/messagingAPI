from flask import Flask

app = Flask(__name__)

from API import API

app.run()