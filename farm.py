"""Split plan.json shots over N workers and render one worker's share.
python3 farm.py run <i> <N>      (reads farm/trigger.txt: 'all' or 'shots=1,5,9')
"""
import json, os, sys, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
T0 = time.time()
LIMIT = 5.3 * 3600   # GitHub jobs are killed at 6 h


def shots_wanted(plan):
    trig = open(os.path.join(HERE, "farm", "trigger.txt")).read().strip().splitlines()[0].split()[0]
    ids = [s["id"] for s in plan["shots"]]
    if trig.startswith("shots="):
        want = []
        for part in trig[6:].split(","):
            if "-" in part:
                a, b = map(int, part.split("-")); want += list(range(a, b + 1))
            elif part:
                want.append(int(part))
        ids = [i for i in ids if i in want]
    return ids


def cost(s):
    n = round((s["t1"] - s["t0"]) * 12)
    close = isinstance(s["cam"], dict) and s["cam"].get("kind") in ("close", "xclose", "medium")
    return 60 + n * (1.0 + 0.35 * len(s["cast"])) * (2.0 if close else 1.0)


def buckets(plan, N):
    want = shots_wanted(plan)
    S = sorted([s for s in plan["shots"] if s["id"] in want], key=cost, reverse=True)
    B = [[0.0, []] for _ in range(N)]
    for s in S:
        b = min(B, key=lambda x: x[0])
        b[0] += cost(s); b[1].append(s["id"])
    return [sorted(b[1]) for b in B]


if __name__ == "__main__":
    plan = json.load(open(os.path.join(HERE, "plan.json")))
    if sys.argv[1] == "show":
        for i, b in enumerate(buckets(plan, int(sys.argv[2]))):
            print(i, b)
        sys.exit()
    i, N = int(sys.argv[2]), int(sys.argv[3])
    mine = buckets(plan, N)[i]
    os.makedirs("out", exist_ok=True); os.makedirs("logs", exist_ok=True)
    log = open(f"logs/worker_{i:02d}.log", "a")
    log.write(f"worker {i}/{N} shots {mine}\n"); log.flush()
    samples = os.environ.get("SAMPLES", "12")
    for sid in mine:
        if os.path.exists(f"out/shot_{sid:03d}.mp4"):
            continue
        if time.time() - T0 > LIMIT:
            log.write(f"time limit, stopping before shot {sid}\n"); break
        t = time.time()
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "shots.py"), str(sid), f"samples={samples}", "out=out"],
                           capture_output=True, text=True)
        ok = os.path.exists(f"out/shot_{sid:03d}.mp4")
        log.write(f"shot {sid} {'OK' if ok else 'FAIL'} {time.time() - t:.0f}s\n")
        if not ok:
            log.write(r.stdout[-3000:] + "\n" + r.stderr[-6000:] + "\n")
        log.flush()
    log.write(f"done {time.time() - T0:.0f}s\n")
