from flask import Flask
from flask import render_template

import glob
import os
import re
import yaml

app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


class Fano:
  def __init__(self, rho, ID, yaml):
    self.rho = rho
    self.ID  = ID

    if "name" in yaml:
      self.name = yaml["name"]

    if isinstance(yaml["description"], str):
      self.description = [self.__parse(yaml["description"])]
    else:
      self.description = [self.__parse(description) for description in yaml["description"]]

    # now do a plaintext version
    if isinstance(yaml["description"], str):
      self.plaintext = self.__parse(yaml["description"], clean=True)
    else:
      self.plaintext = ", ".join([self.__parse(description, clean=True) for description in yaml["description"]])

    if "remarks" in yaml:
      self.remarks = yaml["remarks"]

    self.KX3 = yaml["-KX3"]
    self.h12 = yaml["h12"]
    if isinstance(yaml["moduli"], int):
      self.moduli = [yaml["moduli"]]
    else:
      self.moduli = yaml["moduli"]

    # deal with alternative descriptions
    if "alternative" in yaml:
      self.alternative = [self.__parse(alternative) for alternative in yaml["alternative"]]

    # by default the index is 1
    if "index" in yaml:
      self.index = yaml["index"]
    else:
      self.index = 1

    # if rho = 1 and index = 1 then there is also a genus, from -K_X^3
    if self.rho == 1 and self.index == 1:
      self.genus = (self.KX3 + 2) // 2

    # deal with blowdowns
    self.is_primitive = not "blowdown" in yaml
    if "blowdown" in yaml:
      self.blowdown = yaml["blowdown"]
    else:
      self.blowdown = []

    # deal with (uni)rationality
    self.is_rational = "rational" in yaml and yaml["rational"] == True
    if "rational" in yaml:
      if yaml["rational"] == True: self.rationality = "yes"
      else: self.rationality = yaml["rational"]
    else: self.rationality = "no"

    self.is_unirational = ("unirational" in yaml and yaml["unirational"] == True) or "rational" in yaml
    if "unirational" in yaml:
      if yaml["unirational"] == True: self.unirationality = "yes"
      else: self.unirationality = yaml["unirational"]
    elif self.is_rational: self.unirationality = "yes"
    else: self.unirationality = "no"

    # deal with Mori fibre space candidates (= being fibre-like)
    if self.rho == 1:
      self.fibrelike = True
    else:
      if "fibrelike" in yaml: self.fibrelike = True
      else: self.fibrelike = False

    # deal with Aut^0: (description of group, number of moduli with this group, dimension of group)
    if "Aut" not in yaml:
      self.Aut = [("0", self.moduli[0], 0)]
    else:
      # always read in the Aut
      self.Aut = yaml["Aut"]

      # if the number of moduli for the family is equal to the maximal we assume that there are no trivial Aut^0's in the family
      moduli = [triple[1] for triple in self.Aut]
      if not self.moduli[0] == max(moduli):
        self.Aut.append(("0", self.moduli[0], 0),)


  def __eq__(self, other):
    return self.identifier() == other.identifier()


  # returns the the identifier
  def identifier(self):
    return "{}-{}".format(self.rho, self.ID)

  # process strings
  def __parse(self, string, clean=False):
    if clean:
      replacement = r'\1-\2'
    else:
      replacement = r'<a class="identifier" data-toggle="tooltip" data-placement="bottom" data-html="true" title="\1-\2" href="/\1-\2">\1-\2</a>'

    # weird workaround to deal with ((i-jk))
    string = re.sub(r"\(\((\d)-(\d\d)\)\)", replacement, string)
    return re.sub(r"\(\((\d){1}-(\d){1}\)\)", replacement, string)


# create the dictionary of all deformation families of Fano 3-folds
fanos = {i: dict() for i in range(1, 11)}

with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), "data.yml"), "r") as f:
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

  # postprocessing step to add plaintext tooltips to descriptions
  for rho in fanos.keys():
    for ID in fanos[rho].keys():
      # descriptions
      for i in range(len(fanos[rho][ID].description)):
        for match in re.findall("title=\"(\d+)-(\d+)\"", fanos[rho][ID].description[i]):
          fanos[rho][ID].description[i] = fanos[rho][ID].description[i].replace("title=\"%d-%d\"" % (int(match[0]), int(match[1])), "title='%s'" % fanos[int(match[0])][int(match[1])].plaintext)
      # alternatives
      if hasattr(fanos[rho][ID], "alternative"):
        for i in range(len(fanos[rho][ID].alternative)):
          for match in re.findall("title=\"(\d+)-(\d+)\"", fanos[rho][ID].alternative[i]):
            fanos[rho][ID].alternative[i] = fanos[rho][ID].alternative[i].replace("title=\"%d-%d\"" % (int(match[0]), int(match[1])), "title='%s'" % fanos[int(match[0])][int(match[1])].plaintext)



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


@app.route("/explained")
def show_explained():
  flat = [fano for table in fanos.values() for fano in table.values()]
  # to count totals (as this is hard in the template)
  numbers = dict()
  numbers["total"] = len(flat)
  numbers["primitive"] = len([fano for fano in flat if fano.is_primitive])
  numbers["rational"] = len([fano for fano in flat if fano.is_rational])
  numbers["unirational"] = len([fano for fano in flat if fano.is_unirational])

  return render_template("explained.html", fanos=fanos, numbers=numbers)


@app.route("/about")
def show_about():
  return render_template("about.html", fanos=fanos)



@app.route("/<int:rho>")
def show_table(rho):
  return render_template("table.show.html", fanos=fanos[rho], rho=rho)


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


"""
# Naming scheme

The file data.yml is a YAML file containing all the information on Fano 3-folds we can display here.

The global structure for

Obligatory fields for an entry:
  - description: a human-readable description
  - -KX3
  - h12
  - moduli: the number of moduli

Optional fields for an entry:
  - alternative: a different description of the Fano 3-folds
  - index: if not present, assumed to be 1
  - rational: if not present, assumed to be non-rational, its values can be "yes" or "generic"
  - unirational: if not present, assumed to be non-unirational (unless rational is present), its values can be "yes" or "some"

"""
