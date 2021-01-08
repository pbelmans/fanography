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

    # deal with toric varieties
    if "toric" in yaml:
      self.toric = True
      self.grdb = yaml["toric"]
    else:
      self.toric = False

    # dealing with (links to) period sequences
    if "period" in yaml:
      self.period = True
      self.period_grdb = int(yaml["period"].split(", ")[0])
      self.period_fanosearch = int(yaml["period"].split(", ")[1])
    else:
      self.period = False

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

    # deal with exceptional collections
    if "exceptional" in yaml:
      self.exceptional = yaml["exceptional"]
    # if h^{1,2} but no data present: use Orlov's blowup or projective bundle formula
    elif self.h12 == 0:
      if self.rho == 2 and self.ID in [24, 32, 34, 35, 36]:
        self.exceptional = ["Orlov's projective bundle formula"]
      elif self.rho == 3 and self.ID in [27, 31]:
        self.exceptional = ["Orlov's projective bundle formula"]
      else:
        self.exceptional = ["Orlov's blowup formula"]

    # extremal contractions (only partial information for now)
    self.MMP = []
    if "MMP" in yaml:
      self.MMP = yaml["MMP"]

    # deal with quantum cohomology
    self.qh = []
    if self.h12 == 0:
      # rank 1: TODO figure out good references
      if self.identifier() in ["1-10", "1-15", "1-16", "1-17"]:
          self.qh.append(["small", "someone", "at some point", "?"])

      # Ciolli's one or two curve blowups of P^3 and Q^3
      if self.identifier() in ["2-21", "2-22", "2-26", "2-27", "2-29", "2-30", "2-33", "3-10", "3-12", "3-15", "3-18", "3-20", "3-25"]:
        self.qh.append(["small", "Ciolli", 2005, "MR2168069", "the description of a 1 or 2-curve blowup of $\mathbb{P}^3$ or $Q^3$"])

      # for P^1-bundles Ciolli claims semisimplicity
      if any([contraction[0] == "P1" for contraction in self.MMP]):
        self.qh.append(["small", "Ciolli", 2005, "MR2168069", "the description of quantum cohomology of a $\mathbb{P}^1$-bundle"])

      # Iritani shows (implicitly) semisimplicity of small quantum for Fano toric
      if self.toric:
        self.qh.append(["small", "Iritani", 2007, "MR2359850", "toric geometry"])

    # deal with Hochschild (co)homology
    self.hochschild_homology = [self.h12, 2 + 2*self.rho, self.h12] # degree -1, 0, 1
    if "bivector" not in yaml:
      print("%d-%d: not computed yet" % (self.rho, self.ID))
    else:
      # TODO check H^1(X,T_X) for 1-10
      # TODO improve this
      bivector = yaml["bivector"]
      self.polyvector = [
              [1, 0, 0, 0],
              [self.Aut[-1][2], self.moduli[0], 0, 0],
              [bivector[0], bivector[1], bivector[2], 0],
              [self.KX3 // 2 + 3, 0, 0, 0]]

      self.hochschild_cohomology = [1, self.polyvector[1][0], self.polyvector[1][1] + self.polyvector[2][0], self.polyvector[2][1] + self.polyvector[3][0], self.polyvector[2][2]]


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


class delPezzo:
  def __init__(self, ID, yaml):
    self.ID  = ID

    self.label = yaml["label"]
    self.degree = int(ID[2]) if ID[0:2] == "dP" else 8

    self.name = yaml["name"] if "name" in yaml else ""

    # deal with constructions
    self.anticanonical = yaml["anticanonical"] if yaml["anticanonical"] else ""

    self.intersections = []
    if "intersections" in yaml:
      self.intersections.extend(yaml["intersections"])

    # number of exceptional curves
    self.exceptional = yaml["exceptional"]
    self.rank = 10 - self.degree

    # deal with moduli
    if self.degree >= 5:
      self.moduli = 0
    else:
      self.moduli = (5 - self.degree) * 2

    # deal with automorphism groups: degree 5 and higher is rigid, so there is a unique automorphism group, for lower degrees: it varies in moduli
    if self.degree >= 5:
      self.automorphisms = yaml["Aut"]
    else:
      self.automorphisms = ["finite", 0]

      # deal with the possible finite automorphism groups
      if self.degree <= 4:
        self.groups = yaml["Aut"]["groups"]

    # the anticanonical bundle
    self.index = yaml["index"]
    self.very_ample_power = 1 if self.degree >= 7 else (2 if self.degree == 2 else 3) # evidently I am ambivalent of what is explicit and what not...



# create the dictionary of all deformation families of Fano 3-folds
fanos = {i: dict() for i in range(1, 11)}

with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), "data.yml"), "r", encoding="utf8") as f:
  data = yaml.load(f, Loader=yaml.FullLoader)

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


# add the description as the zero section of a vector bundle from arXiv:2009.13382
with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), "sections.yml"), "r", encoding="utf8") as f:
  data = yaml.load(f, Loader=yaml.FullLoader)

  # read in the data
  for key in data.keys():
    (rho, ID) = (int(key.split("-")[0]), int(key.split("-")[1]))
    fano = fanos[rho][ID]
    fano.sections = data[key]


# create the dictionary of all deformation families of del Pezzo surfaces
delpezzos = dict()

delpezzos_order = ["dP9", "P1xP1", "dP8", "dP7", "dP6", "dP5", "dP4", "dP3", "dP2", "dP1"]

with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), "delpezzo-surfaces.yml"), "r", encoding="utf8") as f:
  data = yaml.load(f, Loader=yaml.FullLoader)

  # read in the data
  for ID in data.keys():
    delpezzos[ID] = delPezzo(ID, data[ID])


flat = [fano for table in fanos.values() for fano in table.values()]
# to count totals (as this is hard in the template)
numbers = dict()
numbers["total"] = len(flat)
numbers["primitive"] = len([fano for fano in flat if fano.is_primitive])
numbers["rational"] = len([fano for fano in flat if fano.is_rational])
numbers["unirational"] = len([fano for fano in flat if fano.is_unirational])
numbers["exceptional"] = len([fano for fano in flat if fano.h12 == 0])
numbers["semisimple"] = len([fano for fano in flat if fano.h12 == 0 and len(fano.qh) > 0])


@app.route("/")
def index():
  return render_template("index.html", fanos=fanos)


@app.route("/explained")
def show_explained():
  return render_template("explained.html", fanos=fanos, numbers=numbers)


@app.route("/about")
def show_about():
  return render_template("about.html", fanos=fanos)



@app.route("/<int:rho>")
def show_table(rho):
  return render_template("table.fanos.html", fanos=fanos[rho], rho=rho)


@app.route("/<int:rho>-<int:ID>")
def show_entry(rho, ID):
  try:
    previous = None
    try: previous = fanos[rho][ID - 1]
    except KeyError:
      try:
        previous = fanos[rho - 1][max(fanos[rho - 1].keys())]
      except KeyError: pass

    next = None
    try: next = fanos[rho][ID + 1]
    except KeyError:
      try:
        next = fanos[rho + 1][1]
      except KeyError: pass

    return render_template("entry.show.html", fano=fanos[rho][ID], previous=previous, next=next)

  except KeyError:
    return render_template("entry.notfound.html", rho=rho, ID=ID)


@app.route("/toric")
def show_toric():
  # let's hardcode the order from Iskovskikh--Prokhorov (this therefore acts as the filtering)
  order = [(1, 17), (2, 36), (2, 35), (2, 33), (2, 34), (3, 31), (3, 29), (3, 30), (3, 27), (3, 28), (3, 26), (3, 25), (4, 12), (4, 11), (4, 10), (4, 9), (5, 3), (5, 2)]

  return render_template("table.toric.html", fanos=fanos, order=order)


@app.route("/delpezzo-varieties")
def show_delpezzovarieties():
  # let's hardcode the order from Iskovskikh--Prokhorov (this therefore acts as the filtering)
  order = [(1, 11, -1), (1, 12, -1), (1, 13, -1), (1, 14, -1), (1, 15, "\leq 6"), (3, 27, 3), (2, 32, "\leq 4"), (2, 35, 3)]

  with open(os.path.join(os.path.realpath(os.path.dirname(__file__)), "delpezzo-varieties.yml"), "r", encoding="utf8") as f:
    data = yaml.load(f)

    # read in the data
    for ID in data.keys():
      order[ID] = (order[ID][0], order[ID][1], order[ID][2], data[ID])

  return render_template("table.delpezzo-varieties.html", fanos=fanos, order=order)


@app.route("/dubrovin")
def show_dubrovin():
  return render_template("table.dubrovin.html", fanos=fanos, numbers=numbers)


@app.route("/zero-section")
def show_zero_section():
  return render_template("table.zero-section.html", fanos=fanos)


@app.route("/delpezzos")
def show_delpezzosurfaces():
  return render_template("table.delpezzo-surfaces.html", delpezzos=delpezzos)


@app.route("/delpezzos/<string:ID>")
def show_delpezzosurface(ID):
  try:
    previous = None
    if delpezzos_order.index(ID) > 0:
      previous = delpezzos[delpezzos_order[delpezzos_order.index(ID) - 1]]

    next = None
    if delpezzos_order.index(ID) < 9:
      next = delpezzos[delpezzos_order[delpezzos_order.index(ID) + 1]]

    return render_template("delpezzo.show.html", delpezzo=delpezzos[ID], previous=previous, next=next)

  except KeyError:
    return render_template("delpezzo.notfound.html", delpezzos=delpezzos, ID=ID)


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
  - toric: if present it refers to the database of smooth toric Fanos on grdb.co.uk

"""
