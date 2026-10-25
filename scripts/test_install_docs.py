#!/usr/bin/env python3
"""Ensure installer documentation never sends agents into slow clone or removed packaging."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
install = (ROOT / "INSTALL.md").read_text("utf-8")
readme = (ROOT / "README.md").read_text("utf-8")
agents = (ROOT / "AGENTS.md").read_text("utf-8")
guide = (ROOT / "使用指南.md").read_text("utf-8")
assert "scripts/quick_install.py" in install
assert "--max-seconds 24" in install
assert "--mirror-url" in install
assert "ghproxy.net" in install
assert "第三方镜像的许可" in install
assert "scripts/package_workbuddy.py" in install and "不存在" in install
assert "[INSTALL.md](INSTALL.md)" in readme
assert "单一路径" in readme
assert "MANDATORY" in agents and "INSTALL.md" in agents
assert "无止境重试" in guide
assert not re.search(r"(?m)^\s*git clone\s+https?://",readme)
assert not re.search(r"(?m)^\s*git clone\s+https?://",install)
assert "--expected-sha256" in install and "--expected-sha256" in readme
assert "可信" in install and "不得运行" in install
assert "scripts/install.py --agent" not in guide
print("INSTALL DOCS CHECK: PASS")
