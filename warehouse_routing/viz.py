"""Pictures: the warehouse with a route, and an animation of the genetic algorithm improving a route."""
from __future__ import annotations

from typing import List, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .layout import Location, Warehouse  # noqa: E402


def _draw(ax, wh: Warehouse, picks: Sequence[Location], route: Sequence[int], title: str):
    img = np.where(wh.grid, 1.0, 0.35)
    ax.imshow(img, cmap="gray", vmin=0, vmax=1)
    cells = [wh.depot] + [picks[i - 1].access for i in route] + [wh.depot]
    pts: List = []
    for a, b in zip(cells, cells[1:]):
        path = wh.shortest_path(a, b)
        pts.extend(path if not pts else path[1:])
    ax.plot([c for _, c in pts], [r for r, _ in pts], color="#d1495b", lw=1.6, alpha=.85)
    ax.scatter([p.cell[1] for p in picks], [p.cell[0] for p in picks], s=28, color="#1d6fb8", zorder=3)
    ax.scatter([wh.depot[1]], [wh.depot[0]], s=90, marker="s", color="#2a9d4a", zorder=4)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])


def plot_route(wh: Warehouse, picks, route, d, path: str, title: str = "") -> None:
    from .algorithms import route_cost
    fig, ax = plt.subplots(figsize=(6, 6 * wh.rows / wh.cols + .6))
    _draw(ax, wh, picks, route, f"{title} - {route_cost(d, route)} steps")
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_compare(wh, picks, d, routes: dict, path: str) -> None:
    from .algorithms import route_cost
    n = len(routes)
    fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 3.2 * wh.rows / wh.cols + .8))
    for ax, (name, r) in zip(np.atleast_1d(axes), routes.items()):
        _draw(ax, wh, picks, r, f"{name}\n{route_cost(d, r)} steps")
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def animate_ga(wh, picks, d, history, path: str, frames: int = 40) -> None:
    """Write a GIF showing the best route found at selected generations."""
    from PIL import Image
    import io
    from .algorithms import route_cost
    idx = sorted(set(np.linspace(0, len(history) - 1, frames).astype(int)))
    imgs = []
    for i in idx:
        gen, route, cost = history[i]
        fig, ax = plt.subplots(figsize=(5, 5 * wh.rows / wh.cols + .6))
        _draw(ax, wh, picks, route, f"Genetic algorithm - generation {gen}: {cost} steps")
        fig.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=80); plt.close(fig)
        buf.seek(0); imgs.append(Image.open(buf).convert("P", palette=Image.ADAPTIVE))
    durations = [120] * (len(imgs) - 1) + [1800]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durations, loop=0)
