"""
Delta Robot — Realistic Engineering Sketch
==========================================
Produces a high-quality pencil/technical-illustration style
rendering of the modular delta robot with shading, depth, and
component callouts.  Saved as a PNG.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Arc, Wedge, Circle, FancyBboxPatch
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.patheffects as pe
from scipy.spatial.transform import Rotation

# ── palette (warm off-white paper look) ──────────────────────
BG        = "#F5F2EB"
INK       = "#1A1714"
STEEL     = "#6B7280"
STEEL_LT  = "#9CA3AF"
STEEL_SH  = "#374151"
GOLD      = "#B45309"
GOLD_LT   = "#D97706"
GREEN     = "#166534"
GREEN_LT  = "#15803D"
BLUE      = "#1E3A5F"
BLUE_LT   = "#2563EB"
PURPLE    = "#4C1D95"
PURPLE_LT = "#7C3AED"
RED_SH    = "#7F1D1D"
ANNOT     = "#374151"
SHADOW    = "#1A1714"

# ─────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────

def rot_z(pts, deg):
    """Rotate Nx3 array around Z axis."""
    a = np.radians(deg)
    R = np.array([[np.cos(a), -np.sin(a), 0],
                  [np.sin(a),  np.cos(a), 0],
                  [0,          0,         1]])
    return pts @ R.T

def project_iso(pts):
    """Simple isometric-ish projection → 2-D (x, y)."""
    # mild perspective: rotate 30° around X, then 45° around Z
    ax = np.radians(28)
    az = np.radians(38)
    Rx = np.array([[1,0,0],[0,np.cos(ax),-np.sin(ax)],[0,np.sin(ax),np.cos(ax)]])
    Rz = np.array([[np.cos(az),-np.sin(az),0],[np.sin(az),np.cos(az),0],[0,0,1]])
    p = pts @ Rx.T @ Rz.T
    return p[:, 0], p[:, 1]

def px(pts):
    x, y = project_iso(np.atleast_2d(pts))
    return x, y


# ─────────────────────────────────────────────────────────────
# Component drawing helpers
# ─────────────────────────────────────────────────────────────

def draw_cylinder_3pts(ax, base, top, radius, color, shade, n=18, alpha=1.0, zorder=3):
    """Draw a cylinder between base and top (3-D pts) projected to 2-D."""
    axis = np.array(top) - np.array(base)
    length = np.linalg.norm(axis)
    if length < 1e-6:
        return
    axis_n = axis / length
    # Perpendicular in world XY
    perp = np.array([-axis_n[1], axis_n[0], 0])
    if np.linalg.norm(perp) < 1e-6:
        perp = np.array([1, 0, 0])
    perp = perp / np.linalg.norm(perp) * radius

    # Four corners of the cylinder strip
    p0 = np.array(base) + perp
    p1 = np.array(base) - perp
    p2 = np.array(top)  - perp
    p3 = np.array(top)  + perp
    pts = np.array([p0, p1, p2, p3, p0])
    x2, y2 = px(pts)
    ax.fill(x2, y2, color=color, alpha=alpha, zorder=zorder)
    ax.plot(x2, y2, color=shade, lw=0.7, alpha=0.9, zorder=zorder+0.1)
    # Highlight edge
    xe, ye = px(np.array([p0, p3]))
    ax.plot(xe, ye, color="white", lw=0.6, alpha=0.5, zorder=zorder+0.2)


def draw_sphere(ax, centre, radius, color, shade, zorder=5):
    """Approximate sphere as filled circle with shading rings."""
    cx, cy = px(np.array([centre]))
    circle = plt.Circle((cx[0], cy[0]), radius * 0.018,
                         color=color, zorder=zorder)
    ax.add_patch(circle)
    # Highlight
    hx = cx[0] - radius * 0.005
    hy = cy[0] + radius * 0.005
    hi = plt.Circle((hx, hy), radius * 0.006,
                    color="white", alpha=0.55, zorder=zorder + 0.1)
    ax.add_patch(hi)
    # Shadow edge
    ring = plt.Circle((cx[0], cy[0]), radius * 0.018,
                       color=shade, fill=False, lw=1.0, zorder=zorder + 0.2)
    ax.add_patch(ring)


def draw_box_3d(ax, centre, dx, dy, dz, color, shade, zorder=3, alpha=1.0):
    """Draw a rectangular box centred at `centre` with half-dims dx,dy,dz."""
    c = np.array(centre)
    corners = np.array([
        c + np.array([ dx,  dy, -dz]),
        c + np.array([-dx,  dy, -dz]),
        c + np.array([-dx, -dy, -dz]),
        c + np.array([ dx, -dy, -dz]),
        c + np.array([ dx,  dy,  dz]),
        c + np.array([-dx,  dy,  dz]),
        c + np.array([-dx, -dy,  dz]),
        c + np.array([ dx, -dy,  dz]),
    ])
    # Faces: bottom, top, front, back, left, right
    faces = [
        [0,1,2,3],   # bottom  (-z)
        [4,5,6,7],   # top     (+z)
        [0,3,7,4],   # front   (+x)
        [1,2,6,5],   # back    (-x)
        [0,1,5,4],   # right   (+y)
        [3,2,6,7],   # left    (-y)
    ]
    shades = [0.55, 1.0, 0.88, 0.50, 0.72, 0.65]
    for face, sh in zip(faces, shades):
        pts_f = corners[face]
        x2, y2 = px(pts_f)
        fc = _shade_color(color, sh)
        ax.fill(x2, y2, color=fc, alpha=alpha, zorder=zorder)
        ax.plot(list(x2) + [x2[0]], list(y2) + [y2[0]],
                color=shade, lw=0.5, zorder=zorder + 0.1)


def _shade_color(hex_color, factor):
    """Lighten/darken a hex colour by factor (1=original, <1=darker, >1=lighter)."""
    import colorsys
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16)/255 for i in (0, 2, 4))
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    v2 = min(1.0, v * factor)
    r2, g2, b2 = colorsys.hsv_to_rgb(hh, s, v2)
    return (r2, g2, b2)


def callout(ax, xy, text, xytext, color=ANNOT):
    ax.annotate(
        text, xy=xy, xytext=xytext,
        fontsize=8.5, color=color,
        fontfamily="DejaVu Sans",
        arrowprops=dict(
            arrowstyle="-",
            color=color,
            lw=0.8,
            connectionstyle="arc3,rad=0.0",
        ),
        bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=color,
                  lw=0.6, alpha=0.92),
        zorder=20,
    )


# ─────────────────────────────────────────────────────────────
# Robot geometry
# ─────────────────────────────────────────────────────────────

Rb   = 1.90    # base radius
Rp   = 0.48    # platform radius
rf   = 1.15    # upper arm
re   = 2.28    # forearm
theta = np.radians(32)   # actuator angle (mid-range pose)

def elbow(arm_idx):
    phi = np.radians(arm_idx * 120)
    ex = (Rb - Rp + rf * np.cos(theta)) * np.cos(phi)
    ey = (Rb - Rp + rf * np.cos(theta)) * np.sin(phi)
    ez = -rf * np.sin(theta)
    return np.array([ex, ey, ez])

def plat_joint(centre, arm_idx):
    phi = np.radians(arm_idx * 120)
    return centre + np.array([Rp * np.cos(phi), Rp * np.sin(phi), 0])

def base_joint(arm_idx):
    phi = np.radians(arm_idx * 120)
    return np.array([Rb * np.cos(phi), Rb * np.sin(phi), 0.0])

# Platform centre (solve analytically for symmetric pose)
e0 = elbow(0)
A  = (Rp - e0[0])**2 + e0[1]**2
cz = e0[2] - np.sqrt(re**2 - A)
platform_centre = np.array([0.0, 0.0, cz])

elbows  = [elbow(i) for i in range(3)]
b_joints = [base_joint(i) for i in range(3)]
p_joints = [plat_joint(platform_centre, i) for i in range(3)]


# ─────────────────────────────────────────────────────────────
# Figure
# ─────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 16), facecolor=BG)
ax.set_facecolor(BG)
ax.set_aspect("equal")
ax.axis("off")

# Subtle grid (paper texture feel)
for v in np.arange(-6, 6, 0.35):
    ax.axhline(v, color="#E8E4DB", lw=0.3, zorder=0)
    ax.axvline(v, color="#E8E4DB", lw=0.3, zorder=0)


# ─── Shadow on ground plane ────────────────────────────────
shadow_y_offset = -0.14
sx, sy = px(np.array([[bj[0], bj[1], -0.05] for bj in b_joints]))
ax.fill(sx, sy + shadow_y_offset, color="#C8C3B5", alpha=0.45,
        zorder=1)

# ─── BASE MOUNTING FRAME ──────────────────────────────────
# Thick triangular plate at z=0
z_plate = 0.08
plate_pts = np.array([b_joints[0], b_joints[1], b_joints[2],
                       b_joints[0]])
# Bottom face of plate
bp = np.array([[b[0], b[1], -z_plate] for b in b_joints])
# Draw top face
top_plate = np.array([b_joints[0], b_joints[1], b_joints[2]])
x2, y2 = px(top_plate)
ax.fill(x2, y2, color=_shade_color(STEEL, 1.05), alpha=1.0, zorder=4)
ax.plot(list(x2) + [x2[0]], list(y2) + [y2[0]],
        color=STEEL_SH, lw=1.4, zorder=4.1)

# Side edges of plate
for i in range(3):
    j = (i + 1) % 3
    side = np.array([
        b_joints[i], b_joints[j],
        [b_joints[j][0], b_joints[j][1], -z_plate],
        [b_joints[i][0], b_joints[i][1], -z_plate],
    ])
    x2, y2 = px(side)
    ax.fill(x2, y2, color=_shade_color(STEEL, 0.72), alpha=1.0, zorder=3.9)
    ax.plot(list(x2)+[x2[0]], list(y2)+[y2[0]], color=STEEL_SH, lw=0.7, zorder=4)

# Mounting holes on base plate
for bj in b_joints:
    hx, hy = px(np.array([[bj[0]*0.78, bj[1]*0.78, 0.085]]))
    hole = plt.Circle((hx[0], hy[0]), 0.028, color=_shade_color(STEEL, 0.5),
                       zorder=5)
    ax.add_patch(hole)

# Central hub body
draw_box_3d(ax, [0, 0, 0.10], 0.30, 0.30, 0.10,
            STEEL, STEEL_SH, zorder=5, alpha=1.0)
draw_box_3d(ax, [0, 0, 0.20], 0.22, 0.22, 0.08,
            _shade_color(STEEL, 0.85), STEEL_SH, zorder=5.1, alpha=1.0)

# ─── R-MODULES (revolute joints at base) ──────────────────
r_mod_r  = 0.14   # module radius
r_mod_h  = 0.22   # module height

for i, bj in enumerate(b_joints):
    # Module body
    draw_cylinder_3pts(ax,
        bj + np.array([0, 0, -r_mod_h/2]),
        bj + np.array([0, 0,  r_mod_h/2]),
        r_mod_r, _shade_color(BLUE, 0.9), BLUE, zorder=6, alpha=1.0)
    # End cap
    cx, cy = px(np.array([bj + np.array([0, 0, r_mod_h/2])]))
    cap = plt.Circle((cx[0], cy[0]), r_mod_r * 0.018,
                     color=_shade_color(BLUE, 1.1), zorder=6.5)
    ax.add_patch(cap)
    cap_ring = plt.Circle((cx[0], cy[0]), r_mod_r * 0.018,
                          color=BLUE, fill=False, lw=0.8, zorder=6.6)
    ax.add_patch(cap_ring)
    # Cable/connector notch
    draw_box_3d(ax, bj + np.array([0, 0, r_mod_h/2 + 0.04]),
                0.04, 0.06, 0.035, _shade_color(BLUE, 0.7), BLUE_LT,
                zorder=6.7)

# ─── UPPER ARMS (L-modules) ─────────────────────────────
arm_w = 0.065

for i in range(3):
    bj = b_joints[i]
    el = elbows[i]
    draw_cylinder_3pts(ax,
        bj + np.array([0, 0, 0]),
        el,
        arm_w, _shade_color(GREEN, 0.95), GREEN_LT,
        zorder=5, alpha=1.0)
    # Highlight stripe along arm
    mid = (bj + el) / 2
    draw_cylinder_3pts(ax, bj, el, arm_w * 0.3,
                       "white", "white", zorder=5.2, alpha=0.18)

# ─── ELBOW S-MODULES ─────────────────────────────────────
for el in elbows:
    draw_sphere(ax, el, 220, _shade_color(GOLD, 1.0), GOLD)
    # Double-cardan inner ring
    cx, cy = px(np.array([el]))
    ring = plt.Circle((cx[0], cy[0]), 220 * 0.013,
                      color=GOLD_LT, fill=False, lw=1.1, zorder=5.5)
    ax.add_patch(ring)
    ring2 = plt.Circle((cx[0], cy[0]), 220 * 0.009,
                       color=GOLD_LT, fill=False, lw=0.6,
                       linestyle="--", zorder=5.5)
    ax.add_patch(ring2)

# ─── FOREARMS — parallelogram pairs ──────────────────────
rod_r  = 0.038
rod_gap = 0.055   # spacing between the two rods of the pair

for i in range(3):
    el = elbows[i]
    pj = p_joints[i]

    # Perpendicular offset direction
    direction = pj - el
    perp3 = np.cross(direction, np.array([0, 0, 1]))
    if np.linalg.norm(perp3) < 1e-6:
        perp3 = np.cross(direction, np.array([1, 0, 0]))
    perp3 = perp3 / np.linalg.norm(perp3) * rod_gap

    for sign in (-1, +1):
        off = perp3 * sign
        draw_cylinder_3pts(ax,
            el + off, pj + off,
            rod_r, _shade_color(GREEN, 1.05), GREEN,
            zorder=4, alpha=1.0)

    # Cross-brace at midpoint
    mid = (el + pj) / 2
    draw_cylinder_3pts(ax,
        mid - perp3, mid + perp3,
        rod_r * 0.7, _shade_color(GREEN, 0.8), GREEN,
        zorder=4.1)

# ─── PLATFORM DISTAL JOINTS ──────────────────────────────
for pj in p_joints:
    draw_sphere(ax, pj, 170, _shade_color(GOLD, 0.9), GOLD_LT)

# ─── MOVING PLATFORM ─────────────────────────────────────
# Triangular plate
plat_top    = np.array(p_joints)
plat_bottom = plat_top + np.array([[0, 0, -0.09]] * 3)
x2, y2 = px(plat_top)
ax.fill(x2, y2, color=_shade_color(BLUE, 1.0), alpha=0.95, zorder=8)
ax.plot(list(x2)+[x2[0]], list(y2)+[y2[0]], color=BLUE, lw=1.2, zorder=8.1)

for i in range(3):
    j = (i+1) % 3
    side = np.array([plat_top[i], plat_top[j],
                     plat_bottom[j], plat_bottom[i]])
    x2s, y2s = px(side)
    ax.fill(x2s, y2s, color=_shade_color(BLUE, 0.72), alpha=0.95, zorder=7.9)
    ax.plot(list(x2s)+[x2s[0]], list(y2s)+[y2s[0]],
            color=BLUE, lw=0.7, zorder=8)

# Platform centre marker
cx, cy = px(np.array([platform_centre]))
ax.scatter(cx, cy, s=30, color=BLUE_LT, zorder=9, marker="o")

# ─── W-MODULE (wrist) ────────────────────────────────────
pc  = platform_centre
draw_box_3d(ax, pc + np.array([0, 0, -0.12]),
            0.18, 0.18, 0.09, PURPLE, PURPLE_LT, zorder=9)
draw_box_3d(ax, pc + np.array([0, 0, -0.22]),
            0.12, 0.12, 0.07, _shade_color(PURPLE, 0.85), PURPLE_LT,
            zorder=9.1)

# ─── END EFFECTOR ────────────────────────────────────────
tip_base = pc + np.array([0, 0, -0.30])
tip_end  = pc + np.array([0, 0, -0.52])
draw_cylinder_3pts(ax, tip_base, tip_end, 0.045,
                   _shade_color(STEEL, 0.8), STEEL_SH, zorder=10)
# Tip cone
tip_pts = np.array([
    tip_end + np.array([0.045,  0, 0]),
    tip_end + np.array([0.045,  0, 0]),
    tip_end + np.array([0,      0, -0.08]),
])
draw_cylinder_3pts(ax, tip_end, tip_end + np.array([0, 0, -0.07]),
                   0.042, _shade_color(STEEL, 0.7), STEEL_SH, zorder=10.1)
# Suction cup
cup_c = tip_end + np.array([0, 0, -0.09])
cx, cy = px(np.array([cup_c]))
cup = plt.Circle((cx[0], cy[0]), 0.024, color=_shade_color(STEEL, 0.5),
                 zorder=11)
ax.add_patch(cup)
cup_r = plt.Circle((cx[0], cy[0]), 0.024, color=STEEL_SH, fill=False,
                   lw=1.0, zorder=11.1)
ax.add_patch(cup_r)

# ─── MOUNTING STRUT (ceiling mount) ──────────────────────
strut_top = np.array([0, 0, 0.55])
draw_cylinder_3pts(ax, np.array([0, 0, 0.28]),
                   strut_top, 0.08,
                   _shade_color(STEEL, 0.88), STEEL_SH,
                   zorder=3, alpha=0.9)

# Ceiling plate
ceil_pts = np.array([
    [-1.2, -1.2, 0.55], [ 1.2, -1.2, 0.55],
    [ 1.2,  1.2, 0.55], [-1.2,  1.2, 0.55],
])
x2, y2 = px(ceil_pts)
ax.fill(x2, y2, color=_shade_color(STEEL, 0.65), alpha=0.55, zorder=2)
ax.plot(list(x2)+[x2[0]], list(y2)+[y2[0]],
        color=STEEL_SH, lw=1.0, alpha=0.7, zorder=2.1)

# Ceiling bolts
for boff in [[-0.9,-0.9,0.55],[0.9,-0.9,0.55],[0.9,0.9,0.55],[-0.9,0.9,0.55]]:
    bx, by = px(np.array([boff]))
    bolt = plt.Circle((bx[0], by[0]), 0.018,
                      color=_shade_color(STEEL, 0.55), zorder=2.5)
    ax.add_patch(bolt)

# ─── CABLE MANAGEMENT ────────────────────────────────────
# Subtle cable from hub to each R-module
for bj in b_joints:
    mid_pt = (bj + np.array([0, 0, 0.28])) / 2 + np.array([0, 0, 0.15])
    cable = np.array([
        [0, 0, 0.22],
        mid_pt,
        bj + np.array([0, 0, 0.12])
    ])
    x2, y2 = px(cable)
    ax.plot(x2, y2, color=_shade_color(STEEL, 0.6), lw=1.1,
            linestyle=(0, (4, 2)), alpha=0.65, zorder=3.5)


# ─────────────────────────────────────────────────────────────
# Callout annotations
# ─────────────────────────────────────────────────────────────

# Precompute projected positions for key points
bj0x, bj0y   = px(np.array([b_joints[0]]))
bj1x, bj1y   = px(np.array([b_joints[1]]))
bj2x, bj2y   = px(np.array([b_joints[2]]))
el0x,  el0y  = px(np.array([elbows[0]]))
el1x,  el1y  = px(np.array([elbows[1]]))
pj0x,  pj0y  = px(np.array([p_joints[0]]))
pj2x,  pj2y  = px(np.array([p_joints[2]]))
pcx,   pcy   = px(np.array([platform_centre]))
arm0mx, arm0my = px(np.array([(b_joints[0] + elbows[0]) / 2]))
fa0mx, fa0my   = px(np.array([(elbows[0] + p_joints[0]) / 2]))
tipx, tipy     = px(np.array([tip_end + np.array([0, 0, -0.09])]))
strutx, struty = px(np.array([[0, 0, 0.42]]))

callout(ax, (bj0x[0], bj0y[0]+0.02), "R-module\n(revolute joint,\nhollow-shafted)",
        (bj0x[0]+0.85, bj0y[0]+0.55), BLUE)

callout(ax, (bj1x[0]-0.02, bj1y[0]),
        "Fixed base frame\n(triangular, ceiling-\nmounted)",
        (bj1x[0]-1.1, bj1y[0]+0.30), STEEL_SH)

callout(ax, (arm0mx[0], arm0my[0]),
        "L-module\n(upper arm,\nrigid/telescoping)",
        (arm0mx[0]-1.05, arm0my[0]+0.20), GREEN)

callout(ax, (el0x[0], el0y[0]),
        "S-module\n(double-cardan\nelbow joint)",
        (el0x[0]+0.85, el0y[0]+0.10), GOLD)

callout(ax, (fa0mx[0], fa0my[0]-0.02),
        "Parallelogram\nforearm pair\n(locks platform rotation)",
        (fa0mx[0]+0.85, fa0my[0]-0.50), GREEN)

callout(ax, (pj0x[0], pj0y[0]),
        "Distal S-module\n(platform spherical\njoint)",
        (pj0x[0]+0.85, pj0y[0]-0.28), GOLD)

callout(ax, (pcx[0], pcy[0]-0.06),
        "Moving platform\n(rigid triangle)",
        (pcx[0]-1.20, pcy[0]-0.45), BLUE)

callout(ax, (pcx[0], pcy[0]-0.20),
        "W-module\n(wrist, 1–3 DOF)",
        (pcx[0]+0.90, pcy[0]-0.55), PURPLE)

callout(ax, (tipx[0], tipy[0]),
        "End-effector\n(vacuum suction cup)",
        (tipx[0]+0.90, tipy[0]-0.18), STEEL_SH)

callout(ax, (strutx[0], struty[0]+0.04),
        "Ceiling mount\n& cable routing",
        (strutx[0]-1.15, struty[0]+0.38), STEEL_SH)


# ─────────────────────────────────────────────────────────────
# Title block
# ─────────────────────────────────────────────────────────────

fig.text(0.50, 0.965, "Modular Delta Robot — Physical Design Sketch",
         ha="center", va="top", fontsize=16, fontweight="700",
         color=INK, fontfamily="DejaVu Sans")
fig.text(0.50, 0.948, "R  ·  L  ·  S  ·  W  module family  |  parallelogram forearms  |  hollow-shaft revolute joints",
         ha="center", va="top", fontsize=9, color=STEEL_SH,
         fontfamily="DejaVu Sans")

# Module legend strip
legend_items = [
    (BLUE,      "R-module  Revolute joint (motorized)"),
    (GREEN,     "L-module  Upper arm link"),
    (GOLD,      "S-module  Spherical / double-cardan joint"),
    (PURPLE,    "W-module  Wrist / tooling head"),
    (STEEL,     "Structural  Frame · platform · struts"),
]
lx = 0.07
for clr, txt in legend_items:
    fig.add_axes([lx, 0.025, 0.012, 0.012]).set_visible(False)
    rect = mpatches.Patch(facecolor=clr, edgecolor=_shade_color(clr, 0.6),
                          linewidth=0.8)
    lx_next = lx + 0.155
    fig.text(lx + 0.014, 0.028, txt, fontsize=8, color=INK,
             fontfamily="DejaVu Sans", va="center")
    # coloured swatch
    sw_ax = fig.add_axes([lx, 0.022, 0.010, 0.014])
    sw_ax.set_facecolor(clr)
    sw_ax.set_xticks([]); sw_ax.set_yticks([])
    for sp in sw_ax.spines.values():
        sp.set_edgecolor(_shade_color(clr, 0.6))
        sp.set_linewidth(0.7)
    lx = lx_next

# Scale bar
ax.annotate("", xy=(3.3, -3.8), xytext=(3.3 + 0.50, -3.8),
            arrowprops=dict(arrowstyle="<->", color=INK, lw=1.0))
ax.text(3.55, -3.72, "500 mm", ha="center", va="bottom",
        fontsize=8, color=INK)

ax.set_xlim(-4.2, 5.0)
ax.set_ylim(-4.5, 3.8)

plt.tight_layout(rect=[0, 0.045, 1, 0.96])
out = "/mnt/user-data/outputs/delta_robot_sketch.png"
fig.savefig(out, dpi=180, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
print(f"Saved → {out}")