"""helper worker: render the shots on line i of farm/help.txt, publishing after each one (branch prepared by the workflow)"""
import os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
i = int(sys.argv[1])
lines = open(os.path.join(HERE, "farm", "help.txt")).read().split("\n")
ids = [int(x) for x in lines[i].split(",") if x.strip()] if i < len(lines) else []
os.makedirs("out", exist_ok=True); os.makedirs("logs", exist_ok=True)
log = open(f"logs/helper_{i:02d}.log", "a")
log.write(f"helper {i} shots {ids}\n"); log.flush()
for sid in ids:
    t = time.time()
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "shots.py"), str(sid), f"samples={os.environ.get('SAMPLES', '12')}", "out=out"],
                       capture_output=True, text=True)
    ok = os.path.exists(f"out/shot_{sid:03d}.mp4")
    log.write(f"shot {sid} {'OK' if ok else 'FAIL'} {time.time() - t:.0f}s\n")
    if not ok:
        log.write(r.stdout[-3000:] + "\n" + r.stderr[-6000:] + "\n")
    log.flush()
    subprocess.run("cp -f out/shot_*.mp4 /tmp/pub/ 2>/dev/null; cp -rf logs /tmp/pub/; cd /tmp/pub && git add -A && "
                   f"git commit -qm 'progress helper {i}' && git push -qf origin HEAD", shell=True)
log.write("done\n"); log.close()
