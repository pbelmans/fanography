from flask import render_template, request, redirect
import yaml

from fanography.application import app, Fano

@app.route("/<string:rho>-<string:ID>")
def show_entry(rho, ID):
  filename = "data/{}-{}.yml".format(rho, ID)
  try:
    with open(filename, "r") as f:
      return render_template("entry.html", fano=Fano(rho, ID, yaml.load(f)))

  except FileNotFoundError:
    pass

