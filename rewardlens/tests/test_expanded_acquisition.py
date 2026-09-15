"""Small CPU-only checks for frozen acquisition identity and scope."""
import hashlib
from pathlib import Path
import tempfile
from scripts.expanded_model_acquire import matches, required_files

def test_identity_and_model_only_files():
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/"weight"
        path.write_bytes(b"abc")
        assert matches(path,{"size":3,"lfs":{"sha256":hashlib.sha256(b"abc").hexdigest()}})
        assert matches(path,{"size":3,"blobId":hashlib.sha1(b"blob 3\0abc").hexdigest()})
        assert not matches(path,{"size":4,"blobId":"bad"})
        path.write_bytes(b"xyz")
        assert not matches(path,{"size":3,"lfs":{"sha256":hashlib.sha256(b"abc").hexdigest()}})
    names=["config.json","model.safetensors","tokenizer.model","data/rows.json","image.jpg"]
    assert [r["rfilename"] for r in required_files({"siblings":[{"rfilename":x} for x in names]})]==names[:3]
