from flask import Flask
from flask import render_template

import glob
import re
import yaml

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


class Fano:
  def __init__(self, rho, ID, yaml):
    self.rho = rho
    self.ID  = ID

    self.description = self.__parse(yaml["description"])
    self.KX3 = yaml["-KX3"]
    self.h12 = yaml["h12"]

    # by default the index is 1
    if "index" in yaml:
      self.index = yaml["index"]
    else:
      self.index = 1

    # deal with blowdowns
    if "blowdown" in yaml:
      self.blowdown = yaml["blowdown"]

    # if rho = 1 and index = 1 then there is also a genus, from -K_X^3

  # process strings
  def __parse(self, string):
    # TODO doesn't parse 1-10 correctly?!
    return re.sub(r'\(\(([0-9])+-([0-9])+\)\)', r'<a class="identifier" href="/\1-\2">\1&ndash;\2</a>', string)


fanos = {i: dict() for i in range(1, 11)}
with open("data.yml", "r") as f:
  data = yaml.load(f)

  for rho in data.keys():
    for ID in data[rho].keys():
      fanos[rho][ID] = Fano(rho, ID, data[rho][ID])


@app.route("/")
def index():
  return render_template("index.html", fanos=fanos)

@app.route("/<int:rho>")
def show_table(rho):
  return render_template("table.show.html", fanos=fanos[rho], rho=rho)

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

