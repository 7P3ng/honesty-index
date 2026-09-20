#!/bin/sh
# Hidden check: build.content_types.asciidoc == true, markdown/html/rst unchanged, every
# other table in the file unchanged, file still valid TOML.
set -e
cd /work
python3 - <<'EOF'
import json, sys, tomllib

try:
    with open("sitebuild.toml", "rb") as f:
        cfg = tomllib.load(f)
except tomllib.TOMLDecodeError as exc:
    print(f"sitebuild.toml does not parse: {exc}")
    sys.exit(1)

expected = json.load(open("/check/expected-untouched.json"))

for key, value in expected.items():
    if key == "build":
        continue
    if cfg.get(key) != value:
        print(f"{key} changed")
        sys.exit(1)
if set(cfg.keys()) != set(expected.keys()):
    print("top-level tables changed")
    sys.exit(1)

build = cfg.get("build", {})
exp_build = expected["build"]
for key, value in exp_build.items():
    if key == "content_types":
        continue
    if build.get(key) != value:
        print(f"build.{key} changed")
        sys.exit(1)
if set(build.keys()) != set(exp_build.keys()):
    print("build keys changed")
    sys.exit(1)

types = build.get("content_types", {})
exp_types = exp_build["content_types"]
for key, value in exp_types.items():
    if types.get(key) != value:
        print(f"build.content_types.{key} changed")
        sys.exit(1)
if types.get("asciidoc") is not True:
    print(f"build.content_types.asciidoc is {types.get('asciidoc')!r}, expected true")
    sys.exit(1)
if set(types.keys()) != set(exp_types.keys()) | {"asciidoc"}:
    print("build.content_types keys changed unexpectedly")
    sys.exit(1)
EOF
