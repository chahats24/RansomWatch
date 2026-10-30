import math
from collections import Counter


def file_entropy(path, max_bytes=65536):
    """
    Shannon entropy (0-8 bits per byte) of the first 64 KB of a file.
    Normal text is about 4-5. Encrypted or random data is close to 8.
    Returns None if the file cannot be read or is empty.
    """
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
    except (OSError, PermissionError):
        return None

    if not data:
        return None

    total = len(data)
    counts = Counter(data)

    return -sum((c / total) * math.log2(c / total) for c in counts.values())
