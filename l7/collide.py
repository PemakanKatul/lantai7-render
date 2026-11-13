"""Report pairs of characters closer than MIN metres at any time inside a shot (plan.json)."""
import json, math, sys
MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.55
plan = json.load(open("plan.json"))


def track(c, dur):
    at = list(c["at"]) if not isinstance(c["at"], str) else None
    if at is None:
        return None
    pts = [(0.0, at[0], at[1], at[2] if len(at) > 2 else 0)]
    for k in sorted([k for k in c.get("keys", []) if k[1] == "move"], key=lambda k: k[0]):
        v = k[2]
        pts.append((k[0], v[0], v[1], v[2]))
    pts.sort()

    def pos(t):
        if t <= pts[0][0]:
            return pts[0][1:]
        for a, b in zip(pts, pts[1:]):
            if a[0] <= t <= b[0]:
                u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
                return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
        return pts[-1][1:]
    return pos


bad = 0
for s in plan["shots"]:
    dur = s["t1"] - s["t0"]
    people = [c for c in s["cast"] if c.get("as", c["who"]) != "hantu" and not c.get("lie")]
    tr = [(c["who"], track(c, dur)) for c in people]
    tr = [x for x in tr if x[1]]
    worst = {}
    for i in range(len(tr)):
        for j in range(i + 1, len(tr)):
            for k in range(0, int(dur * 12) + 1):
                t = k / 12
                a, b = tr[i][1](t), tr[j][1](t)
                if abs(a[2] - b[2]) > 0.6:
                    continue
                d = math.hypot(a[0] - b[0], a[1] - b[1])
                key = (tr[i][0], tr[j][0])
                if d < MIN and d < worst.get(key, (9,))[0]:
                    worst[key] = (round(d, 2), round(t, 2))
    for (a, b), (d, t) in worst.items():
        bad += 1
        print(f"shot {s['id']:3d} seg {s['seg']:2d} w{s['w']:<3d} {a}-{b}: {d} m at t={t}")
print("conflicts:", bad)
