import os
import time

FOLDER = "test_folder"

print()
print("==========================================")
print("   RANSOMWATCH SAFE ATTACK SIMULATION")
print("==========================================")
print("Target folder:", FOLDER)
print()
print("Creating ransomware-like activity...")
print()

files = []

# Create uniquely named test files
for i in range(20):
    filename = f"attack_demo_{i}.txt"
    filepath = os.path.join(FOLDER, filename)

    # If the file already exists, use another name
    counter = 1

    while os.path.exists(filepath):
        filename = f"attack_demo_{i}_{counter}.txt"
        filepath = os.path.join(FOLDER, filename)
        counter += 1

    with open(filepath, "w") as f:
        f.write("Safe RansomWatch simulation file.")

    files.append(filepath)


# Rapidly rename files
for filepath in files:

    new_path = filepath.replace(".txt", ".locked")

    # Make sure destination does not already exist
    counter = 1

    while os.path.exists(new_path):
        new_path = filepath.replace(
            ".txt",
            f"_{counter}.locked"
        )
        counter += 1

    os.rename(filepath, new_path)

    with open(new_path, "a") as f:
        f.write("\nSimulated suspicious modification.")


print()
print("Simulation completed.")
print("Only test_folder was modified.")
print("==========================================")