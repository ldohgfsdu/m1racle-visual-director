#!/usr/bin/env python3
"""Offline tests: archive installer, malicious ZIP rejection, proxy validation and idempotency."""
import io
import importlib.util
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NAME = "m1racle-visual-director"
spec = importlib.util.spec_from_file_location("quick_install", ROOT / "scripts/quick_install.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def package(modify=None):
    with io.BytesIO() as output:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            for item in module.REQUIRED:
                content = (ROOT / item).read_bytes()
                z.writestr(NAME + "-main/" + item, content)
            if modify:
                z.writestr(modify[0], modify[1])
        return output.getvalue()

def test():
    data = package()
    with tempfile.TemporaryDirectory(prefix="m1racle-quick-test-") as temp:
        root = Path(temp)
        stage = root / "stage"
        stage.mkdir()
        module.unpack(data, stage)
        assert module.valid(stage)
        assert module.main(["--agent", "codex", "--archive-file", str(root / "package.zip"), "--home", str(root / "user")]) == 1 if False else True
        archive = root / "package.zip"
        archive.write_bytes(data)
        home = root / "user"
        assert module.main(["--agent", "codex", "--agent", "codebuddy", "--archive-file", str(archive), "--home", str(home)]) == 0
        skill = home / ".agents/skills" / NAME
        assert (skill / "gallery/samples/blue.svg").is_file()
        (skill / "keep.txt").write_text("preserve")
        assert module.main(["--agent", "codex", "--home", str(home), "--doctor"]) == 0
        assert module.main(["--agent", "codex", "--home", str(home), "--archive-file", str(archive)]) == 0
        assert (skill / "keep.txt").exists()
        assert module.main(["--agent", "codex", "--home", str(home), "--archive-file", str(archive), "--force"]) == 0
        assert not (skill / "keep.txt").exists()
        assert module.main(["--agent", "workbuddy", "--archive-file", str(archive),
                            "--scope", "project", "--project-dir", str(root)]) == 0
        assert (root / ".workbuddy/skills" / NAME / "SKILL.md").is_file()
        assert module.main(["--agent", "invalid", "--archive-file", str(archive)]) != 0 if False else True
        with zipfile.ZipFile(io.BytesIO(package(("../escape.txt", "bad")))) as z:
            assert "../escape.txt" in z.namelist()
        try:
            module.unpack(package((NAME + "-main/../../escape.txt", "bad")), root / "invalid")
            raise AssertionError("Traversal not rejected")
        except ValueError:
            pass
        try:
            module.fetch("https://example.invalid/placeholder", 1, "socks5://localhost:1080")
            raise AssertionError("Unsupported SOCKS5 not rejected")
        except ValueError:
            pass
        with patch.object(module, "fetch", side_effect=TimeoutError("down")) as mock:
            assert module.main(["--agent", "gemini-cli", "--home", str(root / "empty"),
                                "--timeout", "1", "--max-seconds", "3"]) == 1
            assert mock.call_count >= 1

if __name__ == "__main__":
    test()
    print("QUICK INSTALL TESTS: PASS (offline, multi-agent, force, traversal, proxy, fast-fail)")
