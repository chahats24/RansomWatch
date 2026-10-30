import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from hashing import calculate_sha256
from entropy import file_entropy
from database import initialize_database, log_event



MONITORED_FOLDER = "test_folder"


class RansomWatchHandler(FileSystemEventHandler):

    def on_created(self, event):

        if event.is_directory:
            return

        file_hash = calculate_sha256(event.src_path)

        print(f"[CREATED] {event.src_path}")
        print(f"          SHA-256: {file_hash}")

        
        log_event(
            event_type="created",
            file_path=event.src_path,
            new_extension=os.path.splitext(event.src_path)[1],
            hash_after=file_hash or "",
            entropy=file_entropy(event.src_path)
        )



    def on_modified(self, event):

        if event.is_directory:
            return

        file_hash = calculate_sha256(event.dest_path)

        print(f"[MODIFIED] {event.src_path}")
        print(f"           SHA-256: {file_hash}")

        
        log_event(
            event_type="modified",
            file_path=event.src_path,
            new_extension=os.path.splitext(event.src_path)[1],
            hash_after=file_hash or "",
            entropy=file_entropy(event.src_path)
        )



    def on_deleted(self, event):

        if event.is_directory:
            return

        print(f"[DELETED] {event.src_path}")

        
        log_event(
            event_type="deleted",
            file_path=event.src_path,
            old_extension=os.path.splitext(event.src_path)[1],
        )



    def on_moved(self, event):

        if event.is_directory:
            return

        old_extension = os.path.splitext(event.src_path)[1]
        new_extension = os.path.splitext(event.dest_path)[1]
        file_hash = calculate_sha256(event.src_path)
        print(
            f"[RENAMED] {event.src_path} → {event.dest_path}"
        )

        print(
            f"           Extension: "
            f"{old_extension} → {new_extension}"
        )

        log_event(
            event_type="renamed",
            file_path=event.dest_path,
            old_path=event.src_path,
            new_path=event.dest_path,
            old_extension=old_extension,
            new_extension=new_extension,
            entropy=file_entropy(event.dest_path),
            hash_after=file_hash or ""
        )


def start_monitor():

    
    initialize_database()

    event_handler = RansomWatchHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        MONITORED_FOLDER,
        recursive=True
    )

    observer.start()

    print()
    print("======================================")
    print("       RANSOMWATCH MONITOR")
    print("======================================")
    print(f"Monitoring folder: {MONITORED_FOLDER}")
    print("Status: ACTIVE")
    print()
    print("Watching for:")
    print("  [+] File creation")
    print("  [~] File modification")
    print("  [-] File deletion")
    print("  [>] File rename")
    print()
    print("Press CTRL+C to stop.")
    print("======================================")
    print()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping RansomWatch...")

        observer.stop()

    observer.join()

    print("RansomWatch stopped.")


if __name__ == "__main__":
    start_monitor()