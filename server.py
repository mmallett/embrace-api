#!/usr/bin/python

import os
import json
from flask import Flask, request, render_template, g, redirect, Response

from models import dynamo

app = Flask(__name__)


db = dynamo.DynamoDB()


@app.route('/')
def index():
    return json.dumps(db.list())

@app.route('/', methods=['POST'])
def post_data():
    db.put(request.json)
    return json.dumps({'created':True}), 201


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):

    HOST, PORT = host, port
    app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

  run()
