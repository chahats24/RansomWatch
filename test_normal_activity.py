
import os
import shutil
import time
import collect

folder = os.path.join("test_folder", "normal_bulk_copy_test")
os.makedirs(folder, exist_ok=True)

try:
    setup, action, params = collect.NORMAL["bulk_copy"](folder)

    print("Normal bulk-copy test")
    print("Parameters:", params)
    setup()

    print("Starting normal file-creation activity...")
    action()

    print("Normal activity test completed.")
finally:
    shutil.rmtree(folder, ignore_errors=True)
    print("Test folder cleaned up.")
