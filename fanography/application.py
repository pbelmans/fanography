from flask import Flask
from flask import render_template

import glob
import yaml

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

class Fano:
  def __init__(self, rho, ID, yaml):
    self.rho = rho
    self.ID  = ID

    self.description = yaml["description"]
    self.KX3 = yaml["-KX3"]
    print(yaml["-KX3"])
    self.h12 = yaml["h12"]

    if index in yaml:
      self.index = yaml["index"]
    else:
      self.index = 1

    # if rho = 1 and index = 1 then there is also a genus, from -K_X^3

@app.route("/")
def index():
  fanos = {i: dict() for i in range(1, 11)}

  for filename in glob.glob("data/*.yml"):
    rho = int(filename.split("/")[1].split("-")[0])
    ID =  int(filename.split("/")[1].split("-")[1].split(".")[0])

    with open(filename, "r") as f:
      fanos[rho][ID] = Fano(rho, ID, yaml.load(f))

  return render_template("index.html", fanos=fanos)

"""
# Naming scheme

The directory data/ contains YAML files

The filename is of the form $rho-$ID.yml, where
  - $rho refers to the Picard rank, from 1 to 10
  - $ID refers to the number in the Iskovskikh--Prokhorov table


Obligatory fields:
  - description
  - -KX3
  - h12

Optional fields:
  - index: if not present, assumed to be 1

"""

import fanography.views.entry

