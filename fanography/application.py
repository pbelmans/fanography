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

    # deal with moduli and automorphisms
    self.moduli = yaml["moduli"]

    # by default the index is 1
    if "index" in yaml:
      self.index = yaml["index"]
    else:
      self.index = 1

    # if rho = 1 and index = 1 then there is also a genus, from -K_X^3
    if self.rho == 1 and self.index == 1:
      self.genus = (self.KX3 + 2) / 2

    # deal with blowdowns
    self.is_primitive = not "blowdown" in yaml
    if "blowdown" in yaml:
      self.blowdown = yaml["blowdown"]
    else:
      self.blowdown = []

  def __eq__(self, other):
    return self.identifier() == other.identifier()

  def identifier(self):
    return "{}-{}".format(self.rho, self.ID) # TODO use this wherever possible!

  # process strings
  def __parse(self, string):
    # TODO doesn't parse 1-10 correctly?!
    return re.sub(r'\(\(([0-9])+-([0-9])+\)\)', r'<a class="identifier" href="/\1-\2">\1&ndash;\2</a>', string)


# create the dictionary of all deformation families of Fano 3-folds
fanos = {i: dict() for i in range(1, 11)}
with open("fanography/data.yml", "r") as f:
  data = yaml.load(f)

  # read in the data
  for rho in data.keys():
    for ID in data[rho].keys():
      fanos[rho][ID] = Fano(rho, ID, data[rho][ID])

  # postprocessing step to replace identifiers by objects in list of blowdowns
  for rho in fanos.keys():
    # these are minimal
    if rho == 1:
      continue

    for ID in fanos[rho].keys():
      fanos[rho][ID].blowdown = [fanos[rho - 1][i] for i in fanos[rho - 1] if "{}-{}".format(rho - 1, i) in fanos[rho][ID].blowdown]

  # determine which Fano varieties can be blown up in an irreducible curve and remain Fano
  for rho in fanos.keys():
    # these cannot be blown up
    if rho == 10:
      fanos[rho][1].blowup = []
      continue

    for ID in fanos[rho].keys():
      fanos[rho][ID].blowup = [fano for fano in fanos[rho + 1].values() if "{}-{}".format(rho, ID) in [blowdown.identifier() for blowdown in fano.blowdown]]


@app.route("/")
def index():
  return render_template("index.html", fanos=fanos)

@app.route("/<int:rho>")
def show_table(rho):
  return render_template("table.show.html", fanos=fanos[rho], rho=rho)

@app.route("/explained")
def show_explained():
  return render_template("explained.html", fanos=fanos)

@app.route("/about")
def show_about():
  return render_template("about.html", fanos=fanos)

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
  - moduli

Optional fields:
  - index: if not present, assumed to be 1

"""

import fanography.views.entry

