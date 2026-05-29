from pathlib import Path
import time


class FileLock:
    """Simple cross-process file lock using lock file.
    Not re-entrant. Use short critical sections only.
    """

    def __init__(self, lock_path: Path, timeout_sec: float = 5 * 60):
        self.lock_path = Path(lock_path)
        self.timeout_sec = timeout_sec

    def acquire(self) -> bool:
        start = time.time()
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        while time.time() - start < self.timeout_sec:
            try:
                # Create exclusively
                fd = self.lock_path.open('x')
                fd.write(str(time.time()))
                fd.close()
                return True
            except FileExistsError:
                time.sleep(0.5)
        return False

    def release(self):
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except Exception:
            pass


