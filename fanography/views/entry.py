from flask import render_template, request, redirect
import yaml

from fanography.application import app, fanos

@app.route("/<int:rho>-<int:ID>")
def show_entry(rho, ID):
  try:
    return render_template("entry.show.html", fano=fanos[rho][ID])

  except KeyError:
    return render_template("entry.notfound.html", rho=rho, ID=ID)

