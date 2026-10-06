/* Warehouse routing in JavaScript - a port of the Python package (same layout, same algorithms). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Routing = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function Warehouse(nAisles, shelfRows) {
    if (nAisles < 2 || shelfRows < 1) throw new Error('bad size');
    this.nAisles = nAisles; this.shelfRows = shelfRows;
    this.rows = shelfRows + 2; this.cols = 3 * nAisles - 2;
    this.grid = [];
    for (var r = 0; r < this.rows; r++) {
      var row = [];
      for (var c = 0; c < this.cols; c++) row.push(r === 0 || r === this.rows - 1 || c % 3 === 0);
      this.grid.push(row);
    }
    this.depot = [this.rows - 1, 0];
    this.locations = [];
    for (var b = 0; b < nAisles - 1; b++) {
      var left = 3 * b + 1, right = 3 * b + 2;
      for (var rr = 1; rr <= shelfRows; rr++) {
        this.locations.push({ id: this.locations.length, cell: [rr, left], access: [rr, left - 1], aisle: b });
        this.locations.push({ id: this.locations.length, cell: [rr, right], access: [rr, right + 1], aisle: b + 1 });
      }
    }
  }
  Warehouse.prototype.bfs = function (src) {
    var R = this.rows, C = this.cols, g = this.grid;
    var dist = new Int32Array(R * C).fill(-1), parent = new Int32Array(R * C).fill(-1);
    var s = src[0] * C + src[1]; dist[s] = 0;
    var q = [s], h = 0, D = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    while (h < q.length) {
      var cur = q[h++], r = (cur / C) | 0, c = cur % C;
      for (var k = 0; k < 4; k++) {
        var nr = r + D[k][0], nc = c + D[k][1];
        if (nr >= 0 && nr < R && nc >= 0 && nc < C && g[nr][nc] && dist[nr * C + nc] < 0) {
          dist[nr * C + nc] = dist[cur] + 1; parent[nr * C + nc] = cur; q.push(nr * C + nc);
        }
      }
    }
    return { dist: dist, parent: parent };
  };
  Warehouse.prototype.path = function (a, b) {
    var C = this.cols, p = this.bfs(a).parent, cur = b[0] * C + b[1], end = a[0] * C + a[1], out = [[b[0], b[1]]];
    while (cur !== end) { cur = p[cur]; out.push([(cur / C) | 0, cur % C]); }
    return out.reverse();
  };

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function randomOrder(wh, n, rng) {
    var idx = wh.locations.map(function (_, i) { return i; });
    for (var i = idx.length - 1; i > 0; i--) { var j = Math.floor(rng() * (i + 1)); var t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    return idx.slice(0, n).sort(function (a, b) { return a - b; }).map(function (i) { return wh.locations[i]; });
  }

  function distanceMatrix(wh, picks) {
    var cells = [wh.depot].concat(picks.map(function (p) { return p.access; }));
    return cells.map(function (s) {
      var d = wh.bfs(s).dist;
      return cells.map(function (t) { return d[t[0] * wh.cols + t[1]]; });
    });
  }

  function routeCost(d, route) {
    if (!route.length) return 0;
    var t = d[0][route[0]] + d[route[route.length - 1]][0];
    for (var i = 0; i + 1 < route.length; i++) t += d[route[i]][route[i + 1]];
    return t;
  }

  function randomRoute(n, rng) {
    var r = []; for (var i = 1; i <= n; i++) r.push(i);
    for (var k = r.length - 1; k > 0; k--) { var j = Math.floor(rng() * (k + 1)); var t = r[k]; r[k] = r[j]; r[j] = t; }
    return r;
  }

  function nearestNeighbour(d) {
    var n = d.length - 1, left = [], cur = 0, route = [];
    for (var i = 1; i <= n; i++) left.push(i);
    while (left.length) {
      var best = left[0];
      for (var k = 1; k < left.length; k++) {
        var j = left[k];
        if (d[cur][j] < d[cur][best] || (d[cur][j] === d[cur][best] && j < best)) best = j;
      }
      route.push(best); left.splice(left.indexOf(best), 1); cur = best;
    }
    return route;
  }

  function sShape(picks) {
    var by = {};
    picks.forEach(function (p, i) { (by[p.aisle] = by[p.aisle] || []).push([p.access[0], i + 1]); });
    var route = [], up = true;
    Object.keys(by).map(Number).sort(function (a, b) { return a - b; }).forEach(function (a) {
      var items = by[a].slice().sort(function (x, y) { return up ? (y[0] - x[0]) || (y[1] - x[1]) : (x[0] - y[0]) || (x[1] - y[1]); });
      items.forEach(function (it) { route.push(it[1]); });
      up = !up;
    });
    return route;
  }

  function twoOpt(d, route) {
    var full = [0].concat(route), m = full.length, improved = true;
    while (improved) {
      improved = false;
      for (var i = 1; i < m - 1; i++) for (var j = i + 1; j < m; j++) {
        var a = full[i - 1], b = full[i], c = full[j], e = j + 1 < m ? full[j + 1] : full[0];
        if (d[a][c] + d[b][e] < d[a][b] + d[c][e]) {
          var seg = full.slice(i, j + 1).reverse();
          for (var k = 0; k < seg.length; k++) full[i + k] = seg[k];
          improved = true;
        }
      }
    }
    return full.slice(1);
  }

  function orOpt(d, route, maxSeg) {
    maxSeg = maxSeg || 3;
    var full = [0].concat(route), improved = true;
    while (improved) {
      improved = false;
      var m = full.length;
      for (var seg = 1; seg <= maxSeg && !improved; seg++) {
        for (var i = 1; i <= m - seg; i++) {
          var prev = full[i - 1], first = full[i], last = full[i + seg - 1], nxt = full[(i + seg) % m];
          var removed = d[prev][first] + d[last][nxt] - d[prev][nxt];
          var rest = full.slice(0, i).concat(full.slice(i + seg)), piece = full.slice(i, i + seg);
          var bestGain = 0, bestK = -1, bestRev = false;
          for (var k = 0; k < rest.length; k++) {
            var u = rest[k], v = rest[(k + 1) % rest.length];
            for (var rv = 0; rv < 2; rv++) {
              var p0 = rv ? piece[piece.length - 1] : piece[0], p1 = rv ? piece[0] : piece[piece.length - 1];
              var added = d[u][p0] + d[p1][v] - d[u][v];
              if (removed - added > bestGain) { bestGain = removed - added; bestK = k; bestRev = !!rv; }
            }
          }
          if (bestK >= 0) {
            if (bestRev) piece = piece.slice().reverse();
            full = rest.slice(0, bestK + 1).concat(piece, rest.slice(bestK + 1));
            improved = true; break;
          }
        }
      }
    }
    return full.slice(1);
  }

  function localSearch(d, route) {
    var best = route.slice();
    for (;;) {
      var cand = orOpt(d, twoOpt(d, best));
      if (routeCost(d, cand) >= routeCost(d, best)) return best;
      best = cand;
    }
  }

  function orderCrossover(p1, p2, rng) {
    var n = p1.length; if (n < 2) return p1.slice();
    var i = Math.floor(rng() * n), j = Math.floor(rng() * n);
    if (i > j) { var t = i; i = j; j = t; }
    var child = new Array(n).fill(null), taken = {};
    for (var k = i; k <= j; k++) { child[k] = p1[k]; taken[p1[k]] = true; }
    var fill = p2.filter(function (g) { return !taken[g]; }), f = 0;
    for (var q = 0; q < n; q++) if (child[q] === null) child[q] = fill[f++];
    return child;
  }

  function mutate(r, rng) {
    r = r.slice(); if (r.length < 2) return r;
    var i = Math.floor(rng() * r.length), j = Math.floor(rng() * r.length);
    if (i > j) { var t = i; i = j; j = t; }
    if (rng() < 0.5) { var x = r[i]; r[i] = r[j]; r[j] = x; }
    else { var seg = r.slice(i, j + 1).reverse(); for (var k = 0; k < seg.length; k++) r[i + k] = seg[k]; }
    return r;
  }

  function geneticAlgorithm(d, opt) {
    opt = opt || {};
    var P = opt.population || 80, G = opt.generations || 200, rng = mulberry32(opt.seed || 1);
    var n = d.length - 1, elite = 2, tour = 3, mrate = 0.25;
    var cost = function (r) { return routeCost(d, r); };
    var pop = (opt.seeds || []).map(function (s) { return s.slice(); }).slice(0, P);
    while (pop.length < P) pop.push(randomRoute(n, rng));
    var best = pop.reduce(function (a, b) { return cost(b) < cost(a) ? b : a; });
    var bestCost = cost(best), history = [{ gen: 0, route: best.slice(), cost: bestCost }];
    if (n <= 2) return { route: best, history: history };
    var pick = function () {
      var w = null;
      for (var i = 0; i < tour; i++) { var c = pop[Math.floor(rng() * pop.length)]; if (w === null || cost(c) < cost(w)) w = c; }
      return w;
    };
    for (var g = 1; g <= G; g++) {
      var sorted = pop.slice().sort(function (a, b) { return cost(a) - cost(b); });
      var next = sorted.slice(0, elite).map(function (r) { return r.slice(); });
      while (next.length < P) {
        var child = orderCrossover(pick(), pick(), rng);
        if (rng() < mrate) child = mutate(child, rng);
        next.push(child);
      }
      pop = next;
      var cand = pop.reduce(function (a, b) { return cost(b) < cost(a) ? b : a; });
      if (cost(cand) < bestCost) { best = cand.slice(); bestCost = cost(cand); }
      history.push({ gen: g, route: best.slice(), cost: bestCost });
    }
    return { route: best, history: history };
  }

  function heldKarp(d, maxPicks) {
    maxPicks = maxPicks || 15;
    var n = d.length - 1; if (n > maxPicks) throw new Error('too many picks');
    if (n === 0) return { route: [], cost: 0 };
    var size = 1 << n, INF = 1e9, dp = new Float64Array(size * n).fill(INF), par = new Int16Array(size * n).fill(-1);
    for (var j = 0; j < n; j++) dp[(1 << j) * n + j] = d[0][j + 1];
    for (var mask = 1; mask < size; mask++) for (var a = 0; a < n; a++) {
      var cur = dp[mask * n + a]; if (cur >= INF || !((mask >> a) & 1)) continue;
      for (var b = 0; b < n; b++) {
        if ((mask >> b) & 1) continue;
        var nm = mask | (1 << b), v = cur + d[a + 1][b + 1];
        if (v < dp[nm * n + b]) { dp[nm * n + b] = v; par[nm * n + b] = a; }
      }
    }
    var full = size - 1, bj = 0, bc = INF;
    for (var e = 0; e < n; e++) { var c = dp[full * n + e] + d[e + 1][0]; if (c < bc) { bc = c; bj = e; } }
    var route = [], m = full, jj = bj;
    while (jj !== -1) { route.push(jj + 1); var pj = par[m * n + jj]; m ^= 1 << jj; jj = pj; }
    return { route: route.reverse(), cost: bc };
  }

  return { Warehouse: Warehouse, mulberry32: mulberry32, randomOrder: randomOrder, distanceMatrix: distanceMatrix,
    routeCost: routeCost, randomRoute: randomRoute, nearestNeighbour: nearestNeighbour, sShape: sShape,
    twoOpt: twoOpt, orOpt: orOpt, localSearch: localSearch, geneticAlgorithm: geneticAlgorithm, heldKarp: heldKarp };
});
