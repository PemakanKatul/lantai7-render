# lantai7-render
Render farm for the clay animation "Lantai Tujuh Tidak Pernah Kosong".
Edit `farm/trigger.txt` (`all workers=20` or `shots=1,2,5-9 workers=3`) and push to start a render.
Each worker pushes its finished shots to branch `out-<i>`.
