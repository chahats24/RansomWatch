"""
One-off demo for the review: runs ONE attack-like scenario on dummy files
inside test_folder (nothing is logged to runs.csv) and cleans up afterwards.

  python demo_attack.py                  # random mode
  python demo_attack.py atk_random_names
Modes: atk_inplace, atk_inplace_locked, atk_random_names, atk_copy_delete, atk_partial_locked
"""
import os
import random
import shutil
import sys
import time

import collect

name = sys.argv[1] if len(sys.argv) > 1 else random.choice(list(collect.ATTACK))
folder = os.path.join(collect.BASE, "demo_" + str(int(time.time())))
os.makedirs(folder, exist_ok=True)

setup, action, params = collect.ATTACK[name](folder)
print(f"Preparing dummy files ({name}) ...")
setup()
print("Waiting 8 seconds, then starting the attack-like activity ...")
time.sleep(8)
print("ATTACK STARTED", params)
action()
print("Attack-like activity finished. Cleaning up in 10 seconds ...")
time.sleep(10)
shutil.rmtree(folder, ignore_errors=True)
print("Done. Only dummy files inside", folder, "were touched.")
