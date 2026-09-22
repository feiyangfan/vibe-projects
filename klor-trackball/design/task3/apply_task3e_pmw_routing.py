#!/usr/bin/env python3
"""Task 3E: deterministically route the frozen PMW3360 interface.

Input is the exact Task 3D PCB. The router is intentionally local and
clearance-aware; it may add only J4 interface copper/vias. Existing geometry is
not moved or rewritten.

The committed PCB keeps KiCad zone-fill caches stripped.
"""
from __future__ import annotations

import heapq
import math
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
PCB = ROOT / "PCB/konrad_trackball/konrad_trackball.kicad_pcb"

BASELINE_BLOB = "4272f9c3895fd46c0688b3eb530fc7299b540727"

# Custom-rule minima from konrad_trackball.kicad_dru.
TRACK_CLEAR = 0.127
TRACK_PAD_CLEAR = 0.200
TRACK_PTH_HOLE_CLEAR = 0.330
HOLE_HOLE_CLEAR = 0.500
EDGE_TRACK_CLEAR = 0.300

GRID = 1.0
X0, X1 = 104.0, 150.5
Y0, Y1 = 61.0, 144.0
LAYERS = ("F.Cu", "B.Cu")

# U1 right-side through-hole pad -> J4 through-hole pad.
SIGNALS = {
    85: dict(name="PMW_SCK",  start=(105.318815, 68.195745), end=(147.724665, 134.747997), width=0.254),
    84: dict(name="PMW_MOSI", start=(105.318815, 70.735745), end=(147.724665, 137.287997), width=0.254),
    83: dict(name="PMW_MISO", start=(105.318815, 73.275745), end=(147.724665, 139.827997), width=0.254),
    82: dict(name="PMW_CS",   start=(105.318815, 85.975745), end=(147.724665, 142.367997), width=0.254),
}

# Power is explicitly tied to nearby already-routed same-net geometry.
POWER = {
    3: dict(name="VCC", start=(147.724665, 129.667997), end=(145.840675, 127.985612), width=0.381),
    1: dict(name="GND", start=(147.724665, 127.127997), end=(149.555000, 117.370000), width=0.381),
}

# Start with the three upper SPI pads, then CS. This order preserves the
# narrowest U1 escape channels first.
SIGNAL_ORDER = (85, 84, 83, 82)


@dataclass(frozen=True)
class Segment:
    a: tuple[float, float]
    b: tuple[float, float]
    width: float
    layer: str
    net: int


@dataclass(frozen=True)
class Via:
    p: tuple[float, float]
    size: float
    drill: float
    net: int


@dataclass(frozen=True)
class Pad:
    p: tuple[float, float]
    size: tuple[float, float]
    angle: float
    drill: float
    net: int | None
    ref: str


@dataclass
class Route:
    net: int
    name: str
    width: float
    segments: list[Segment]
    vias: list[Via]


def git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)], cwd=REPO, check=True,
        text=True, capture_output=True,
    ).stdout.strip()


def balanced(text: str, start: int) -> tuple[str, int]:
    depth = 0
    quoted = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1], i + 1
    raise ValueError("unbalanced KiCad expression")


def blocks(text: str, token: str) -> list[str]:
    result = []
    pos = 0
    needle = "(" + token
    while True:
        pos = text.find(needle, pos)
        if pos < 0:
            return result
        block, end = balanced(text, pos)
        result.append(block)
        pos = end


def atom_point(block: str, name: str) -> tuple[float, float] | None:
    m = re.search(rf"\({name}\s+([-\d.]+)\s+([-\d.]+)\)", block)
    return None if not m else (float(m.group(1)), float(m.group(2)))


def top_at(block: str) -> tuple[float, float, float] | None:
    m = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", block)
    return None if not m else (float(m.group(1)), float(m.group(2)), float(m.group(3) or 0.0))


def ref_of(block: str) -> str | None:
    m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
    if not m:
        m = re.search(r'\(fp_text\s+reference\s+"([^"]+)"', block)
    return None if not m else m.group(1)


def net_of(block: str) -> int | None:
    m = re.search(r"\(net\s+(\d+)(?:\s+\"[^\"]*\")?\)", block)
    return None if not m else int(m.group(1))


def layer_of(block: str) -> str | None:
    m = re.search(r'\(layer\s+"([^"]+)"\)', block)
    return None if not m else m.group(1)


def parse_segments(text: str) -> list[Segment]:
    result = []
    for b in blocks(text, "segment"):
        a, z = atom_point(b, "start"), atom_point(b, "end")
        w = re.search(r"\(width\s+([-\d.]+)\)", b)
        layer, net = layer_of(b), net_of(b)
        if a and z and w and layer and net is not None:
            result.append(Segment(a, z, float(w.group(1)), layer, net))
    return result


def parse_vias(text: str) -> list[Via]:
    result = []
    for b in blocks(text, "via"):
        at = top_at(b)
        size = re.search(r"\(size\s+([-\d.]+)\)", b)
        drill = re.search(r"\(drill\s+([-\d.]+)\)", b)
        net = net_of(b)
        if at and size and drill and net is not None:
            result.append(Via((at[0], at[1]), float(size.group(1)), float(drill.group(1)), net))
    return result


def parse_pads(text: str) -> list[Pad]:
    result = []
    for fp in blocks(text, "footprint"):
        fa = top_at(fp)
        ref = ref_of(fp) or "?"
        if fa is None:
            continue
        ft = math.radians(fa[2])
        for p in blocks(fp, "pad"):
            pa = top_at(p)
            size = re.search(r"\(size\s+([-\d.]+)\s+([-\d.]+)\)", p)
            if pa is None or size is None:
                continue
            px, py = pa[0], pa[1]
            gx = fa[0] + px * math.cos(ft) + py * math.sin(ft)
            gy = fa[1] - px * math.sin(ft) + py * math.cos(ft)
            # KiCad board rotation convention matches the transform above.
            angle = fa[2] + pa[2]
            dm = re.search(r"\(drill(?:\s+oval)?\s+([-\d.]+)(?:\s+([-\d.]+))?\)", p)
            drill = 0.0 if dm is None else max(float(dm.group(1)), float(dm.group(2) or dm.group(1)))
            result.append(Pad(
                (gx, gy),
                (float(size.group(1)), float(size.group(2))),
                angle,
                drill,
                net_of(p),
                ref,
            ))
    return result


def sampled_edge_loops(text: str) -> list[list[tuple[float, float]]]:
    pieces: list[tuple[tuple[float,float], tuple[float,float], list[tuple[float,float]]]] = []
    for b in blocks(text, "gr_line"):
        if '(layer "Edge.Cuts")' not in b:
            continue
        a, z = atom_point(b, "start"), atom_point(b, "end")
        if a and z:
            pieces.append((a, z, [a, z]))
    for b in blocks(text, "gr_curve"):
        if '(layer "Edge.Cuts")' not in b:
            continue
        pts = [(float(x), float(y)) for x,y in re.findall(r"\(xy\s+([-\d.]+)\s+([-\d.]+)\)", b)]
        if len(pts) != 4:
            continue
        sampled = []
        for i in range(13):
            t = i / 12
            u = 1 - t
            sampled.append((
                u**3*pts[0][0] + 3*u*u*t*pts[1][0] + 3*u*t*t*pts[2][0] + t**3*pts[3][0],
                u**3*pts[0][1] + 3*u*u*t*pts[1][1] + 3*u*t*t*pts[2][1] + t**3*pts[3][1],
            ))
        pieces.append((pts[0], pts[3], sampled))

    def key(p):
        return (round(p[0], 4), round(p[1], 4))

    adjacency: dict[tuple[float,float], list[int]] = {}
    for i,(a,z,_) in enumerate(pieces):
        adjacency.setdefault(key(a), []).append(i)
        adjacency.setdefault(key(z), []).append(i)

    unused = set(range(len(pieces)))
    loops = []
    while unused:
        seed = unused.pop()
        a,z,pts = pieces[seed]
        start, current, previous = a, z, seed
        chain = list(pts)
        for _ in range(500):
            if key(current) == key(start):
                loops.append(chain)
                break
            options = [i for i in adjacency.get(key(current), []) if i != previous and i in unused]
            if not options:
                break
            i = options[0]
            unused.remove(i)
            aa,zz,pp = pieces[i]
            forward = key(aa) == key(current)
            ordered = pp if forward else list(reversed(pp))
            chain.extend(ordered[1:])
            current = zz if forward else aa
            previous = i
    return loops


def polygon_area(poly):
    return 0.5 * sum(
        poly[j][0]*poly[i][1] - poly[i][0]*poly[j][1]
        for i,j in ((i, i-1) for i in range(len(poly)))
    )


def inside_polygon(p, poly):
    x,y = p
    inside = False
    j = len(poly)-1
    for i in range(len(poly)):
        xi,yi = poly[i]
        xj,yj = poly[j]
        if (yi > y) != (yj > y):
            if x < (xj-xi)*(y-yi)/(yj-yi) + xi:
                inside = not inside
        j = i
    return inside


def point_segment_distance(p, a, b):
    vx,vy = b[0]-a[0], b[1]-a[1]
    wx,wy = p[0]-a[0], p[1]-a[1]
    d = vx*vx + vy*vy
    t = 0.0 if d == 0 else max(0.0, min(1.0, (wx*vx+wy*vy)/d))
    q = (a[0]+t*vx, a[1]+t*vy)
    return math.dist(p, q)


def orientation(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def segments_intersect(a, b, c, d):
    eps = 1e-9
    o1,o2,o3,o4 = orientation(a,b,c), orientation(a,b,d), orientation(c,d,a), orientation(c,d,b)
    if (o1 > eps and o2 < -eps or o1 < -eps and o2 > eps) and \
       (o3 > eps and o4 < -eps or o3 < -eps and o4 > eps):
        return True
    # Collinear/touching cases matter for copper clearance.
    def on(p, q, r):
        return min(p[0],r[0])-eps <= q[0] <= max(p[0],r[0])+eps and \
               min(p[1],r[1])-eps <= q[1] <= max(p[1],r[1])+eps
    if abs(o1) <= eps and on(a,c,b): return True
    if abs(o2) <= eps and on(a,d,b): return True
    if abs(o3) <= eps and on(c,a,d): return True
    if abs(o4) <= eps and on(c,b,d): return True
    return False


def segment_segment_distance(a, b, c, d):
    if segments_intersect(a,b,c,d):
        return 0.0
    return min(
        point_segment_distance(a,c,d),
        point_segment_distance(b,c,d),
        point_segment_distance(c,a,b),
        point_segment_distance(d,a,b),
    )


def segment_hits_inflated_pad(a, b, pad: Pad, inflate: float) -> bool:
    # Transform route segment into the pad's local frame, then test against
    # an axis-aligned rectangle expanded by the required copper clearance.
    theta = math.radians(-pad.angle)
    def local(p):
        dx,dy = p[0]-pad.p[0], p[1]-pad.p[1]
        return (
            dx*math.cos(theta) - dy*math.sin(theta),
            dx*math.sin(theta) + dy*math.cos(theta),
        )
    aa,bb = local(a),local(b)
    hx = pad.size[0]/2 + inflate
    hy = pad.size[1]/2 + inflate
    if abs(aa[0]) <= hx and abs(aa[1]) <= hy:
        return True
    if abs(bb[0]) <= hx and abs(bb[1]) <= hy:
        return True
    corners = [(-hx,-hy),(hx,-hy),(hx,hy),(-hx,hy)]
    return any(
        segments_intersect(aa,bb,corners[i],corners[(i+1)%4])
        for i in range(4)
    )


def rotated_rect_distance(p, pad: Pad) -> float:
    # Conservative rectangular envelope of the copper pad.
    theta = math.radians(-pad.angle)
    dx,dy = p[0]-pad.p[0], p[1]-pad.p[1]
    x = dx*math.cos(theta) - dy*math.sin(theta)
    y = dx*math.sin(theta) + dy*math.cos(theta)
    ox = max(abs(x) - pad.size[0]/2, 0.0)
    oy = max(abs(y) - pad.size[1]/2, 0.0)
    return math.hypot(ox, oy)


def route_length(route: Route) -> float:
    return sum(math.dist(s.a, s.b) for s in route.segments)


def make_router(text: str):
    all_segments = parse_segments(text)
    all_vias = parse_vias(text)
    all_pads = parse_pads(text)

    # Only obstacles near the routing window can matter.
    margin = 5.0
    segments = [
        s for s in all_segments
        if max(s.a[0],s.b[0]) >= X0-margin and min(s.a[0],s.b[0]) <= X1+margin
        and max(s.a[1],s.b[1]) >= Y0-margin and min(s.a[1],s.b[1]) <= Y1+margin
    ]
    vias = [v for v in all_vias if X0-margin <= v.p[0] <= X1+margin and Y0-margin <= v.p[1] <= Y1+margin]
    pads = [p for p in all_pads if X0-margin <= p.p[0] <= X1+margin and Y0-margin <= p.p[1] <= Y1+margin]

    # Spatially index static obstacles. The original implementation scanned
    # every retained track/pad/via for every A* node; this index preserves the
    # exact same clearance tests while reducing each node to nearby objects.
    BUCKET = 4.0
    segment_index: dict[tuple[str,int,int], list[Segment]] = {}
    via_index: dict[tuple[int,int], list[Via]] = {}
    pad_index: dict[tuple[int,int], list[Pad]] = {}

    def bucket_span(lo: float, hi: float):
        return range(math.floor(lo / BUCKET), math.floor(hi / BUCKET) + 1)

    for seg in segments:
        expand = 1.0
        for bx in bucket_span(min(seg.a[0],seg.b[0])-expand, max(seg.a[0],seg.b[0])+expand):
            for by in bucket_span(min(seg.a[1],seg.b[1])-expand, max(seg.a[1],seg.b[1])+expand):
                segment_index.setdefault((seg.layer,bx,by), []).append(seg)

    for via in vias:
        expand = via.drill/2 + HOLE_HOLE_CLEAR + 0.3
        for bx in bucket_span(via.p[0]-expand, via.p[0]+expand):
            for by in bucket_span(via.p[1]-expand, via.p[1]+expand):
                via_index.setdefault((bx,by), []).append(via)

    for pad in pads:
        expand_x = pad.size[0]/2 + 1.0
        expand_y = pad.size[1]/2 + 1.0
        if pad.drill:
            expand_x = max(expand_x, pad.drill/2 + HOLE_HOLE_CLEAR + 0.3)
            expand_y = max(expand_y, pad.drill/2 + HOLE_HOLE_CLEAR + 0.3)
        for bx in bucket_span(pad.p[0]-expand_x, pad.p[0]+expand_x):
            for by in bucket_span(pad.p[1]-expand_y, pad.p[1]+expand_y):
                pad_index.setdefault((bx,by), []).append(pad)

    def cell(p):
        return (math.floor(p[0]/BUCKET), math.floor(p[1]/BUCKET))

    def segment_candidates(p, layer):
        bx,by = cell(p)
        return segment_index.get((layer,bx,by), ())

    def via_candidates(p):
        return via_index.get(cell(p), ())

    def pad_candidates(p):
        return pad_index.get(cell(p), ())

    loops = sampled_edge_loops(text)
    if not loops:
        raise ValueError("no Edge.Cuts loop")
    outer = max(loops, key=lambda p: abs(polygon_area(p)))
    edges = list(zip(outer, outer[1:]))

    nx = round((X1-X0)/GRID)+1
    ny = round((Y1-Y0)/GRID)+1

    def coord(i,j):
        return (X0+i*GRID, Y0+j*GRID)

    def snap(p):
        return (round((p[0]-X0)/GRID), round((p[1]-Y0)/GRID))

    def path_segment_candidates(a, b, layer):
        found = set()
        for bx in bucket_span(min(a[0],b[0])-1.0, max(a[0],b[0])+1.0):
            for by in bucket_span(min(a[1],b[1])-1.0, max(a[1],b[1])+1.0):
                found.update(segment_index.get((layer,bx,by), ()))
        return found

    def path_via_candidates(a, b):
        found = set()
        for bx in bucket_span(min(a[0],b[0])-1.0, max(a[0],b[0])+1.0):
            for by in bucket_span(min(a[1],b[1])-1.0, max(a[1],b[1])+1.0):
                found.update(via_index.get((bx,by), ()))
        return found

    def path_pad_candidates(a, b):
        found = set()
        for bx in bucket_span(min(a[0],b[0])-2.5, max(a[0],b[0])+2.5):
            for by in bucket_span(min(a[1],b[1])-2.5, max(a[1],b[1])+2.5):
                found.update(pad_index.get((bx,by), ()))
        return found

    def track_segment_clear(a, b, layer, net, width, reserved):
        if not inside_polygon(a,outer) or not inside_polygon(b,outer):
            return False
        edge_need = EDGE_TRACK_CLEAR + width/2
        if any(segment_segment_distance(a,b,c,d) < edge_need for c,d in edges):
            return False
        for seg in path_segment_candidates(a,b,layer):
            if seg.net != net and segment_segment_distance(a,b,seg.a,seg.b) < width/2 + seg.width/2 + TRACK_CLEAR:
                return False
        for via in path_via_candidates(a,b):
            if via.net != net and point_segment_distance(via.p,a,b) < via.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2:
                return False
        for pad in path_pad_candidates(a,b):
            if pad.net == net:
                continue
            if segment_hits_inflated_pad(a,b,pad,TRACK_PAD_CLEAR + width/2):
                return False
            if pad.drill and point_segment_distance(pad.p,a,b) < pad.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2:
                return False
        for route in reserved:
            if route.net == net:
                continue
            for seg in route.segments:
                if seg.layer == layer and segment_segment_distance(a,b,seg.a,seg.b) < width/2 + seg.width/2 + TRACK_CLEAR:
                    return False
            for via in route.vias:
                if point_segment_distance(via.p,a,b) < via.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2:
                    return False
        return True

    def track_point_clear(p, layer, net, width, reserved):
        if not inside_polygon(p, outer):
            return False
        edge_need = EDGE_TRACK_CLEAR + width/2
        if any(point_segment_distance(p,a,b) < edge_need for a,b in edges):
            return False
        for s in segment_candidates(p,layer):
            if s.net != net and point_segment_distance(p,s.a,s.b) < width/2 + s.width/2 + TRACK_CLEAR:
                return False
        for v in via_candidates(p):
            if v.net != net:
                need = v.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2
                if math.dist(p,v.p) < need:
                    return False
        for pad in pad_candidates(p):
            if pad.net == net:
                continue
            if rotated_rect_distance(p,pad) < TRACK_PAD_CLEAR + width/2:
                return False
            if pad.drill and math.dist(p,pad.p) < pad.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2:
                return False
        for r in reserved:
            if r.net == net:
                continue
            for s in r.segments:
                if s.layer == layer and point_segment_distance(p,s.a,s.b) < width/2+s.width/2+TRACK_CLEAR:
                    return False
            for v in r.vias:
                if math.dist(p,v.p) < v.drill/2 + TRACK_PTH_HOLE_CLEAR + width/2:
                    return False
        return True

    def via_clear(p, net, reserved):
        # New via matches the existing compact board convention.
        new = Via(p, 0.4, 0.3, net)
        if not inside_polygon(p, outer):
            return False
        if any(point_segment_distance(p,a,b) < EDGE_TRACK_CLEAR + new.size/2 for a,b in edges):
            return False
        for layer in LAYERS:
            for s in segment_candidates(p,layer):
                if s.net != net and point_segment_distance(p,s.a,s.b) < new.drill/2 + TRACK_PTH_HOLE_CLEAR + s.width/2:
                    return False
        for v in via_candidates(p):
            if v.net != net and math.dist(p,v.p) < new.drill/2 + v.drill/2 + HOLE_HOLE_CLEAR:
                return False
        for pad in pad_candidates(p):
            if pad.net == net:
                continue
            if rotated_rect_distance(p,pad) < TRACK_PAD_CLEAR + new.size/2:
                return False
            if pad.drill and math.dist(p,pad.p) < new.drill/2 + pad.drill/2 + HOLE_HOLE_CLEAR:
                return False
        for r in reserved:
            if r.net == net:
                continue
            for s in r.segments:
                if point_segment_distance(p,s.a,s.b) < new.drill/2 + TRACK_PTH_HOLE_CLEAR + s.width/2:
                    return False
            for v in r.vias:
                if math.dist(p,v.p) < new.drill/2 + v.drill/2 + HOLE_HOLE_CLEAR:
                    return False
        return True

    def movement_clear(a, b, layer, net, width, reserved):
        # GRID is small; endpoints + midpoint are sufficient for the raster
        # search, followed by exact whole-route validation below.
        mid = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        return (
            track_point_clear(a,layer,net,width,reserved)
            and track_point_clear(mid,layer,net,width,reserved)
            and track_point_clear(b,layer,net,width,reserved)
        )

    def route_one(net, spec, reserved):
        start, target, width = spec["start"], spec["end"], spec["width"]
        si,sj = snap(start)
        ti,tj = snap(target)
        if not (X0 <= start[0] <= X1 and Y0 <= start[1] <= Y1
                and X0 <= target[0] <= X1 and Y0 <= target[1] <= Y1):
            raise ValueError("route endpoint outside search window")

        via_cache: dict[tuple[float,float], bool] = {}

        def cached_via_clear(p):
            k = (round(p[0],3), round(p[1],3))
            if k not in via_cache:
                via_cache[k] = via_clear(p,net,reserved)
            return via_cache[k]

        def ident(i,j,l):
            return (l*ny+j)*nx+i

        def decode(v):
            i = v % nx
            q = v // nx
            j = q % ny
            l = q // ny
            return i,j,l

        total = nx*ny*2
        inf = float("inf")
        g = [inf]*total
        previous = [-1]*total
        closed = bytearray(total)
        heap = []

        def heuristic(i,j):
            return math.dist(coord(i,j),target) / GRID

        # The electrical endpoints are exact through-hole pad centers and do
        # not generally lie on the routing raster. Seed every nearby grid node
        # that has an exact legal segment from the pad center.
        seeded = 0
        for layer_index in range(2):
            for di in range(-2,3):
                for dj in range(-2,3):
                    i,j = si+di,sj+dj
                    if not (0 <= i < nx and 0 <= j < ny):
                        continue
                    p = coord(i,j)
                    if math.dist(start,p) > 1.75*GRID:
                        continue
                    if not track_segment_clear(start,p,LAYERS[layer_index],net,width,reserved):
                        continue
                    u = ident(i,j,layer_index)
                    cost = math.dist(start,p) / GRID
                    if cost < g[u]:
                        g[u] = cost
                        heapq.heappush(heap,(cost+heuristic(i,j),u))
                        seeded += 1
        if seeded == 0:
            raise RuntimeError(f"{spec['name']}: no legal raster escape from exact start pad")

        directions = ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
        end = -1
        visited = 0

        while heap:
            _, current = heapq.heappop(heap)
            if closed[current]:
                continue
            closed[current] = 1
            visited += 1
            i,j,l = decode(current)
            a = coord(i,j)
            # Finish through an exact legal segment to the J4/power anchor.
            # The destination pad is through-hole, so either copper layer is
            # valid and no extra via is required at the endpoint.
            if math.dist(a,target) <= 1.75*GRID and \
               track_segment_clear(a,target,LAYERS[l],net,width,reserved):
                end = current
                break
            for di,dj in directions:
                ni,nj = i+di,j+dj
                if not (0 <= ni < nx and 0 <= nj < ny):
                    continue
                b = coord(ni,nj)
                if not track_segment_clear(a,b,LAYERS[l],net,width,reserved):
                    continue
                nxt = ident(ni,nj,l)
                ng = g[current] + math.hypot(di,dj)
                if ng < g[nxt]:
                    g[nxt] = ng
                    previous[nxt] = current
                    heapq.heappush(heap,(ng+heuristic(ni,nj),nxt))

            if cached_via_clear(a):
                nxt = ident(i,j,1-l)
                ng = g[current] + 8.0
                if ng < g[nxt]:
                    g[nxt] = ng
                    previous[nxt] = current
                    heapq.heappush(heap,(ng+heuristic(i,j),nxt))

        if end < 0:
            raise RuntimeError(f"{spec['name']}: no legal route; visited {visited} states")

        states = []
        current = end
        while current >= 0:
            i,j,l = decode(current)
            states.append((coord(i,j),l))
            current = previous[current]
        states.reverse()
        if math.dist(states[0][0],start) > 1e-6:
            states.insert(0,(start,states[0][1]))
        else:
            states[0] = (start,states[0][1])
        if math.dist(states[-1][0],target) > 1e-6:
            states.append((target,states[-1][1]))
        else:
            states[-1] = (target,states[-1][1])

        result = Route(net,spec["name"],width,[],[])
        run_start = states[0][0]
        layer = states[0][1]
        last_direction = None

        for k in range(1,len(states)):
            prev_p,prev_l = states[k-1]
            p,l = states[k]
            if l != prev_l:
                if math.dist(run_start,prev_p) > 1e-6:
                    result.segments.append(Segment(run_start,prev_p,width,LAYERS[layer],net))
                result.vias.append(Via(prev_p,0.4,0.3,net))
                run_start = p
                layer = l
                last_direction = None
                continue
            direction = (round(math.copysign(1,p[0]-prev_p[0])) if p[0]!=prev_p[0] else 0,
                         round(math.copysign(1,p[1]-prev_p[1])) if p[1]!=prev_p[1] else 0)
            if last_direction is not None and direction != last_direction:
                result.segments.append(Segment(run_start,prev_p,width,LAYERS[layer],net))
                run_start = prev_p
            last_direction = direction

        if math.dist(run_start,states[-1][0]) > 1e-6:
            result.segments.append(Segment(run_start,states[-1][0],width,LAYERS[layer],net))

        # Exact post-check on every simplified segment. This also catches
        # any long collinear merge that would cross an obstacle even though its
        # individual raster steps were legal.
        for seg in result.segments:
            if not track_segment_clear(seg.a,seg.b,seg.layer,net,width,reserved):
                raise RuntimeError(
                    f"{spec['name']}: exact clearance failure on {seg}"
                )
        print(f"{spec['name']}: {len(result.segments)} segments, {len(result.vias)} vias, {route_length(result):.3f} mm")
        return result

    return route_one


def kicad_segment(s: Segment, uid: str) -> str:
    return (
        f'(segment\n\t\t(start {s.a[0]:.6f} {s.a[1]:.6f})\n'
        f'\t\t(end {s.b[0]:.6f} {s.b[1]:.6f})\n'
        f'\t\t(width {s.width:.3f})\n\t\t(layer "{s.layer}")\n'
        f'\t\t(net {s.net})\n\t\t(uuid "{uid}")\n\t)'
    )


def kicad_via(v: Via, uid: str) -> str:
    return (
        f'(via\n\t\t(at {v.p[0]:.6f} {v.p[1]:.6f})\n'
        f'\t\t(size {v.size:.3f})\n\t\t(drill {v.drill:.3f})\n'
        f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net {v.net})\n'
        f'\t\t(uuid "{uid}")\n\t)'
    )


def uid(kind: str, net: int, index: int) -> str:
    # Stable UUIDv5 gives deterministic output without hand-maintaining IDs.
    return str(uuid.uuid5(uuid.UUID("3e3e0000-0000-4000-8000-000000000000"), f"{kind}:{net}:{index}"))


def main() -> int:
    if git_blob(PCB) != BASELINE_BLOB:
        raise SystemExit("Task 3E generator requires the exact Task 3D PCB baseline")

    text = PCB.read_text(encoding="utf-8")
    if "(filled_polygon" in text:
        raise SystemExit("zone-fill cache must be stripped before Task 3E")

    route_one = make_router(text)
    routes: list[Route] = []

    for net in SIGNAL_ORDER:
        routes.append(route_one(net,SIGNALS[net],routes))

    # Power routes are intentionally last because PMW timing nets own the
    # hardest escape corridors. Same-net existing copper remains reusable.
    for net in (3,1):
        routes.append(route_one(net,POWER[net],routes))

    # Freeze MOTION as a no-net: J4 pad 5 must still contain no net atom.
    j4 = next((b for b in blocks(text,"footprint") if ref_of(b) == "J4"), None)
    if j4 is None:
        raise SystemExit("J4 missing")
    p5 = [p for p in blocks(j4,"pad") if re.match(r'\(pad\s+"5"',p)]
    if len(p5) != 1 or net_of(p5[0]) is not None:
        raise SystemExit("J4.5 MOTION is no longer NC")

    additions = []
    for r in routes:
        for i,s in enumerate(r.segments,1):
            additions.append(kicad_segment(s,uid("segment",r.net,i)))
        for i,v in enumerate(r.vias,1):
            additions.append(kicad_via(v,uid("via",r.net,i)))

    marker = "\n\t(zone"
    pos = text.find(marker)
    if pos < 0:
        marker = "\n\t(group"
        pos = text.find(marker)
    if pos < 0:
        raise SystemExit("unable to locate top-level insertion point")

    text = text[:pos] + "\n\t" + "\n\t".join(additions) + text[pos:]
    PCB.write_text(text,encoding="utf-8")

    print(f"Task 3E inserted {sum(len(r.segments) for r in routes)} segments and {sum(len(r.vias) for r in routes)} vias")
    print(f"PCB blob: {git_blob(PCB)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
