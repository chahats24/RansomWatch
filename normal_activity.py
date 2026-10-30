import os
import time
import random

FOLDER = "test_folder"

os.makedirs(FOLDER, exist_ok=True)

print("Generating normal file activity...")
print("Press CTRL+C to stop.\n")

while True:

    # Create a normal file
    filename = f"normal_{random.randint(1, 1000)}.txt"
    filepath = os.path.join(FOLDER, filename)

    with open(filepath, "w") as f:
        f.write("Normal user activity in RansomWatch.\n")

    print("[CREATED]", filename)

    time.sleep(random.randint(3, 8))

    # Modify the file
    with open(filepath, "a") as f:
        f.write("Additional normal content.\n")

    print("[MODIFIED]", filename)

    time.sleep(random.randint(3, 8))

    # Occasionally delete the file
    if random.random() < 0.3:
        os.remove(filepath)
        print("[DELETED]", filename)

    time.sleep(random.randint(2, 6))