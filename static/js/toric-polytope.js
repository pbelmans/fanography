(function () {
  "use strict";

  var svgNamespace = "http://www.w3.org/2000/svg";

  function rotate(vertex, angleX, angleY) {
    var cosY = Math.cos(angleY);
    var sinY = Math.sin(angleY);
    var x = cosY * vertex[0] + sinY * vertex[2];
    var z = -sinY * vertex[0] + cosY * vertex[2];
    var cosX = Math.cos(angleX);
    var sinX = Math.sin(angleX);

    return [x, cosX * vertex[1] - sinX * z, sinX * vertex[1] + cosX * z];
  }

  function element(name, attributes) {
    var node = document.createElementNS(svgNamespace, name);
    Object.keys(attributes).forEach(function (key) {
      node.setAttribute(key, attributes[key]);
    });
    return node;
  }

  function initialise(container) {
    var vertices = JSON.parse(container.dataset.vertices);
    var faces = JSON.parse(container.dataset.faces);
    var svg = container.querySelector("svg");
    var angleX = -0.48;
    var angleY = 0.68;
    var drag = null;

    function draw() {
      var rotated = vertices.map(function (vertex) {
        return rotate(vertex, angleX, angleY);
      });
      var xs = rotated.map(function (vertex) { return vertex[0]; });
      var ys = rotated.map(function (vertex) { return vertex[1]; });
      var minX = Math.min.apply(null, xs);
      var maxX = Math.max.apply(null, xs);
      var minY = Math.min.apply(null, ys);
      var maxY = Math.max.apply(null, ys);
      var scale = Math.min(190 / Math.max(maxX - minX, 0.1), 160 / Math.max(maxY - minY, 0.1));
      var centreX = (minX + maxX) / 2;
      var centreY = (minY + maxY) / 2;
      var projected = rotated.map(function (vertex) {
        return [130 + scale * (vertex[0] - centreX), 110 - scale * (vertex[1] - centreY), vertex[2]];
      });
      var orderedFaces = faces.map(function (face) {
        return {
          indices: face,
          depth: face.reduce(function (sum, index) { return sum + projected[index][2]; }, 0) / face.length
        };
      }).sort(function (left, right) { return left.depth - right.depth; });
      var depths = orderedFaces.map(function (face) { return face.depth; });
      var minDepth = Math.min.apply(null, depths);
      var maxDepth = Math.max.apply(null, depths);

      svg.replaceChildren();

      orderedFaces.forEach(function (face) {
        var lightness = 85 - 22 * (face.depth - minDepth) / Math.max(maxDepth - minDepth, 0.1);
        var points = face.indices.map(function (index) {
          return projected[index][0].toFixed(2) + "," + projected[index][1].toFixed(2);
        }).join(" ");
        svg.appendChild(element("polygon", {
          points: points,
          fill: "hsl(343 55% " + lightness.toFixed(1) + "%)",
          stroke: "#621027",
          "stroke-width": "1.5",
          "stroke-linejoin": "round"
        }));
      });

      projected.forEach(function (vertex) {
        svg.appendChild(element("circle", {
          cx: vertex[0].toFixed(2),
          cy: vertex[1].toFixed(2),
          r: "2.8",
          fill: "#3d0918"
        }));
      });
    }

    svg.addEventListener("pointerdown", function (event) {
      drag = {x: event.clientX, y: event.clientY, angleX: angleX, angleY: angleY};
      svg.setPointerCapture(event.pointerId);
    });

    svg.addEventListener("pointermove", function (event) {
      if (!drag) return;
      angleY = drag.angleY + (event.clientX - drag.x) * 0.012;
      angleX = drag.angleX - (event.clientY - drag.y) * 0.012;
      draw();
    });

    function stopDragging() {
      drag = null;
    }

    svg.addEventListener("pointerup", stopDragging);
    svg.addEventListener("pointercancel", stopDragging);

    draw();
  }

  function initialiseAll() {
    document.querySelectorAll(".toric-polytope").forEach(initialise);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseAll);
  } else {
    initialiseAll();
  }
}());
