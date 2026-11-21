#!/usr/bin/env bash
# Run every automated test. Works in Termux (Node is optional).
cd "$(dirname "$0")/.." || exit 1
PY="$(command -v python3 || command -v python)"
status=0
"$PY" -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -n 4 || status=1
if command -v node >/dev/null 2>&1; then
  node tests/test_markdown.js || status=1
else
  echo "node not found: skipping Markdown tests (pkg install nodejs to run them)"
fi
exit $status
