from flask import render_template, request, redirect
import yaml

from fanography.application import app, fanos

@app.route("/<int:rho>-<int:ID>")
def show_entry(rho, ID):
  try:
    previous = None
    try: previous = fanos[rho][ID - 1]
    except KeyError: pass

    next = None
    try: next = fanos[rho][ID + 1]
    except KeyError: pass

    return render_template("entry.show.html", fano=fanos[rho][ID], previous=previous, next=next)

  except KeyError:
    return render_template("entry.notfound.html", rho=rho, ID=ID)
