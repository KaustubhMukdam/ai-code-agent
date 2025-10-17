from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import time
import sys

INPUT_DIR = "data/input"

class AssignmentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".txt"):
            return
        print(f"New job detected: {event.src_path}")
        subprocess.run([sys.executable, "test_graph.py", event.src_path])


if __name__ == "__main__":
    observer = Observer()
    handler = AssignmentHandler()
    observer.schedule(handler, path=INPUT_DIR, recursive=False)
    observer.start()
    print(f"Watching {INPUT_DIR} for jobs...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
