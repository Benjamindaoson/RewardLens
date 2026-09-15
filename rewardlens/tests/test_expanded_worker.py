"""No GPU calls: reject incomplete receipts and honor exclusive model locks."""
import fcntl
import json
from pathlib import Path
import tempfile
from scripts.expanded_worker import valid_full,candidates
from scripts.phase2_autonomous import sha

def check():
    assert len(candidates())==4
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        assert valid_full(root) is False
        (root/"completion.json").write_text(json.dumps({"complete":True,"artifacts":{}}))
        try:
            valid_full(root)
        except ValueError:
            pass
        else:
            raise AssertionError("incomplete receipt accepted")
        with (root/"lock").open("a") as first,(root/"lock").open("a") as second:
            fcntl.flock(first,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                fcntl.flock(second,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise AssertionError("duplicate writer accepted")
    print("EXPANDED_WORKER_RECEIPT_LOCK_PASS")

if __name__=="__main__":
    check()
