"""Render a still of a set (and optional cast) for checking.
python3 -I rt_preview.py '<json shot fragment>' out.png [samples] [frame]
fragment keys: set, cam, cast, extras, dyn  (same format as plan shots; t0=0, t1=duration)
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import shots

frag = json.loads(sys.argv[1])
out = sys.argv[2]
shots.SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 8
frame = int(sys.argv[4]) if len(sys.argv) > 4 else 1
shot = dict(id=999, t0=0.0, t1=frag.get("dur", 2.0), cast=[], dyn=[], extras=[], move="static", sfx=[], music=[], fx=[])
shot.update(frag)
sc, cam, dyn, actors = shots.build(shot)
sc.render.resolution_percentage = int(frag.get("pct", 50))
sc.frame_set(frame)
sc.render.filepath = os.path.abspath(out)
bpy.ops.render.render(write_still=True)
print("WROTE", out)
