"""
RansomWatch labeled-data collector.

Run monitor.py in another terminal first.

  python collect.py auto --runs 40
      Runs a random mix of normal and attack-like scenarios on DUMMY files.

  python collect.py manual 0 20 real_usage
      Records a 20-minute window labeled 0 (normal) while YOU use files
      inside test_folder yourself (copy, edit, unzip, etc.).

Every run is written to data/runs.csv with its start/end time and label.
All files are created by this script inside test_folder/run_<id>/ and are
deleted again afterwards. Nothing outside that folder is touched.
"""
import argparse
import csv
import os
import random
import shutil
import string
import tempfile
import time
import zipfile
from datetime import datetime

def rename_retry(src, dst, tries=30, delay=0.3):
    """Rename that waits out temporary Windows file locks."""
    for i in range(tries):
        try:
            os.rename(src, dst)
            return
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(delay)

BASE = "test_folder"
RUNS_CSV = "data/runs.csv"
GAP = 8  # quiet seconds before/after each run (must be longer than a 5 s window)

WORDS = ("report budget meeting project data summary quarter client review plan "
         "design update status notes draft final version team system network "
         "security file backup policy access user admin record invoice").split()
VICTIM_EXTS = [".txt", ".docx", ".pdf", ".xlsx", ".pptx", ".jpg", ".md"]
LOCK_EXTS = [".locked", ".enc", ".crypt", ".xyz", ".WNCRY"]


# ---------------------------------------------------------------- helpers
def text_bytes(n):
    out, size = [], 0
    while size < n:
        w = random.choice(WORDS)
        out.append(w)
        size += len(w) + 1
    return " ".join(out).encode()[:n]


def write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def rand_name(k=16):
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))


def safe(folder, path):
    """Refuse to touch anything outside this run's folder."""
    root = os.path.abspath(folder)
    p = os.path.abspath(path)
    assert p == root or p.startswith(root + os.sep), f"refusing path outside run folder: {p}"
    return path


def make_victims(folder, n):
    files = []
    for i in range(n):
        p = os.path.join(folder, f"file_{i:03d}{random.choice(VICTIM_EXTS)}")
        write(safe(folder, p), text_bytes(random.randint(8000, 40000)))
        files.append(p)
    return files


# ------------------------------------------------------- normal scenarios
def sc_edit_docs(folder):
    files = []

    def setup():
        files.extend(make_victims(folder, random.randint(3, 8)))

    def action():
        for _ in range(random.randint(10, 18)):
            p = random.choice(files)
            with open(safe(folder, p), "ab") as f:
                f.write(text_bytes(random.randint(200, 2000)))
            time.sleep(random.uniform(1, 3))
    return setup, action, {"files": "3-8"}


def sc_bulk_copy(folder):
    n = random.randint(30, 150)
    delay = random.choice([0, 0.01, 0.05])

    def action():
        for i in range(n):
            write(safe(folder, os.path.join(folder, f"copy_{i}.txt")),
                  text_bytes(random.randint(3000, 20000)))
            time.sleep(delay)
    return (lambda: None), action, {"n": n, "delay": delay}


def sc_photo_import(folder):
    n = random.randint(20, 80)
    delay = random.choice([0, 0.02, 0.1])

    def action():
        for i in range(n):
            write(safe(folder, os.path.join(folder, f"IMG_{i:04d}.jpg")),
                  os.urandom(random.randint(40000, 200000)))
            time.sleep(delay)
    return (lambda: None), action, {"n": n, "delay": delay}


def sc_zip_create(folder):
    k = random.randint(2, 5)

    def action():
        for z in range(k):
            path = os.path.join(folder, f"archive_{z}.zip")
            with zipfile.ZipFile(safe(folder, path), "w", zipfile.ZIP_DEFLATED) as zf:
                for j in range(random.randint(5, 15)):
                    zf.writestr(f"doc_{j}.txt", text_bytes(20000))
            time.sleep(random.uniform(2, 5))
    return (lambda: None), action, {"zips": k}


def sc_unzip(folder):
    n = random.randint(30, 120)
    tmp = tempfile.mkdtemp()
    zpath = os.path.join(tmp, "bundle.zip")

    def setup():
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for j in range(n):
                zf.writestr(f"item_{j}.txt", text_bytes(random.randint(3000, 15000)))

    def action():
        dest = os.path.join(folder, "extracted")
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(safe(folder, dest))
        shutil.rmtree(tmp, ignore_errors=True)
    return setup, action, {"n": n}


def sc_batch_rename(folder):
    n = random.randint(20, 60)
    delay = random.choice([0, 0.02, 0.05])
    files = []

    def setup():
        for i in range(n):
            p = os.path.join(folder, f"IMG_{rand_name(6)}.txt")
            write(safe(folder, p), text_bytes(5000))
            files.append(p)

    def action():
        for i, p in enumerate(files):
            os.rename(safe(folder, p), safe(folder, os.path.join(folder, f"report_{i:03d}.txt")))
            time.sleep(delay)
    return setup, action, {"n": n, "delay": delay}


def sc_delete_cleanup(folder):
    n = random.randint(20, 80)
    files = []

    def setup():
        for i in range(n):
            p = os.path.join(folder, f"tmp_{i}.tmp")
            write(safe(folder, p), text_bytes(4000))
            files.append(p)

    def action():
        for p in files:
            os.remove(safe(folder, p))
            time.sleep(random.choice([0, 0.02]))
    return setup, action, {"n": n}


def sc_mixed_slow(folder):
    pool = []

    def action():
        end = time.time() + random.randint(25, 40)
        while time.time() < end:
            r = random.random()
            if r < 0.4 or not pool:
                p = os.path.join(folder, f"note_{rand_name(5)}.txt")
                write(safe(folder, p), text_bytes(random.randint(2000, 9000)))
                pool.append(p)
            elif r < 0.85:
                with open(safe(folder, random.choice(pool)), "ab") as f:
                    f.write(text_bytes(500))
            else:
                p = pool.pop(random.randrange(len(pool)))
                os.remove(safe(folder, p))
            time.sleep(random.uniform(1, 3))
    return (lambda: None), action, {}


# -------------------------------------------------- attack-like scenarios
# These overwrite DUMMY files (created by this script) with random bytes to
# imitate encryption. No real encryption, no keys, nothing outside run folder.
def _attack(mode):
    def factory(folder):
        n = random.randint(20, 120)
        delay = random.choice([0, 0.02, 0.1, 0.4, 1.0])
        if delay >= 0.4:
            n = min(n, 40)
        ext = random.choice(LOCK_EXTS)
        files = []

        def setup():
            files.extend(make_victims(folder, n))

        def action():
            for p in files:
                size = os.path.getsize(safe(folder, p))
                if mode == "inplace":
                    write(p, os.urandom(size))
                elif mode == "inplace_locked":
                    write(p, os.urandom(size))
                    rename_retry(p, safe(folder, p + ext))
                elif mode == "random_names":
                    write(p, os.urandom(size))
                    os.rename(p, safe(folder, os.path.join(folder, rand_name() + ext)))
                elif mode == "copy_delete":
                    write(safe(folder, p + ext), os.urandom(size))
                    os.remove(p)
                elif mode == "partial_locked":
                    with open(p, "rb") as f:
                        data = f.read()
                    cut = max(1, int(len(data) * 0.3))
                    write(p, os.urandom(cut) + data[cut:])
                    os.rename(p, safe(folder, p + ext))
                time.sleep(delay)
        return setup, action, {"n": n, "delay": delay, "ext": ext}
    return factory


NORMAL = {
    "edit_docs": sc_edit_docs,
    "bulk_copy": sc_bulk_copy,
    "photo_import": sc_photo_import,
    "zip_create": sc_zip_create,
    "unzip": sc_unzip,
    "batch_rename": sc_batch_rename,
    "delete_cleanup": sc_delete_cleanup,
    "mixed_slow": sc_mixed_slow,
}
ATTACK = {
    "atk_inplace": _attack("inplace"),
    "atk_inplace_locked": _attack("inplace_locked"),
    "atk_random_names": _attack("random_names"),
    "atk_copy_delete": _attack("copy_delete"),
    "atk_partial_locked": _attack("partial_locked"),
}


# ------------------------------------------------------------ run control
def log_run(session, label, scenario, start, end, params):
    os.makedirs("data", exist_ok=True)
    new = not os.path.exists(RUNS_CSV)
    with open(RUNS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["session_id", "label", "scenario", "start", "end", "params"])
        w.writerow([session, label, scenario, start.isoformat(), end.isoformat(), params])


def run_one(name, label, factory):
    session = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + name
    folder = os.path.join(BASE, "run_" + session)
    os.makedirs(folder, exist_ok=True)

    setup, action, params = factory(folder)
    setup()
    time.sleep(GAP)                      # quiet gap: setup events are NOT labeled

    start = datetime.now()
    action()
    time.sleep(1.5)                      # let the monitor log the last events
    end = datetime.now()
    log_run(session, label, name, start, end, params)

    time.sleep(GAP)
    shutil.rmtree(folder, ignore_errors=True)   # cleanup (in the gap, not labeled)
    time.sleep(GAP)
    return session


def auto(runs):
    names = []
    for i in range(runs):
        pool = NORMAL if i % 2 == 0 else ATTACK
        names.append(random.choice(list(pool)))
    random.shuffle(names)

    for i, name in enumerate(names, 1):
        label = 1 if name.startswith("atk_") else 0
        factory = ATTACK[name] if label else NORMAL[name]
        print(f"[{i}/{len(names)}] {name:20s} label={label}", flush=True)
        try:
            run_one(name, label, factory)
        except PermissionError as e:
            print(f"  skipped {name} (file locked): {e}")
    print("Done. Runs saved to", RUNS_CSV)


def manual(label, minutes, name):
    print(f"Recording {minutes} min as label={label} ({name}).")
    print("Use files INSIDE test_folder now (copy, edit, unzip...). Ctrl+C to stop early.")
    time.sleep(GAP)
    start = datetime.now()
    try:
        time.sleep(minutes * 60)
    except KeyboardInterrupt:
        pass
    end = datetime.now()
    log_run("manual_" + start.strftime("%Y%m%d_%H%M%S"), label, name, start, end, "manual")
    print("Saved.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auto"); a.add_argument("--runs", type=int, default=40)
    a.add_argument("--gap", type=int, default=GAP)
    m = sub.add_parser("manual")
    m.add_argument("label", type=int); m.add_argument("minutes", type=float); m.add_argument("name")
    args = ap.parse_args()

    if args.cmd == "auto":
        GAP = max(7, args.gap)
        auto(args.runs)
    else:
        manual(args.label, args.minutes, args.name)
