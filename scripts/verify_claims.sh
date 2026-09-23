#!/bin/bash
set -euo pipefail

CLAIMS_FILE="$HOME/proyectos/nlp/docs/claims.json"
DB_PATH="/sdcard/Download/analisis_consolidado.duckdb"

if [ ! -f "$CLAIMS_FILE" ]; then
    echo "No existe: $CLAIMS_FILE"
    exit 2
fi

python3 << PYEOF
import json
import subprocess
import sys
from pathlib import Path

claims_file = Path("$CLAIMS_FILE")
db_path = "$DB_PATH"

data = json.loads(claims_file.read_text(encoding="utf-8"))
claims = data.get("claims", [])
failed = 0
passed = 0

for claim in claims:
    claim_id = claim.get("id", "sin-id")
    source = claim.get("source", "")
    expected = claim.get("value")

    if source.startswith("duckdb:"):
        query = source[len("duckdb:"):].strip()
        cmd = ["duckdb", "-noheader", "-list", db_path, query]
    elif source.startswith("bash:"):
        cmd = ["bash", "-c", source[len("bash:"):].strip()]
    else:
        print(f"WARN {claim_id}: source desconocido")
        failed += 1
        continue

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except Exception as e:
        print(f"WARN {claim_id}: {e}")
        failed += 1
        continue

    if result.returncode != 0:
        print(f"FAIL {claim_id}: exit {result.returncode}")
        failed += 1
        continue

    lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
    if not lines:
        print(f"WARN {claim_id}: sin salida")
        failed += 1
        continue

    actual = lines[-1]

    if str(actual) == str(expected):
        print(f"OK   {claim_id}: {actual}")
        passed += 1
    else:
        print(f"FAIL {claim_id}: esperado {expected!r}, actual {actual!r}")
        failed += 1

print()
print(f"Total: {passed + failed} | Pasaron: {passed} | Fallaron: {failed}")

sys.exit(0 if failed == 0 else 1)
PYEOF

exit $?
