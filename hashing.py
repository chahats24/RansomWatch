import hashlib
import os


def calculate_sha256(file_path):
    """
    Calculate the SHA-256 hash of a file.
    Returns None if the file cannot be accessed.
    """

    if not os.path.exists(file_path):
        return None

    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(4096)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    except (PermissionError, OSError):
        return None

if __name__ == "__main__":
    test_file = "test_folder/test.txt"

    with open(test_file, "w") as file:
        file.write("Hello RansomWatch! This file has changed.")

    file_hash = calculate_sha256(test_file)

    print("File:", test_file)
    print("SHA-256:", file_hash)  