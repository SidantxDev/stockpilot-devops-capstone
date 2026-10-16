#!/usr/bin/env bash
# End-to-end API check against any running StockPilot (compose, kind or EKS).
#
#   ./scripts/smoke-test.sh http://localhost:3000
#   ./scripts/smoke-test.sh http://<traefik-nlb-hostname>
set -euo pipefail

BASE="${1:-http://localhost:3000}"
SKU="SMOKE-$(date +%s)"
pass() { printf '  \033[32m✔\033[0m %s\n' "$*"; }

echo "Smoke testing $BASE"

curl -fsS "$BASE/api/products" >/dev/null && pass "GET    /api/products"
curl -fsS "$BASE/api/products/stats" >/dev/null && pass "GET    /api/products/stats"

ID=$(curl -fsS -X POST "$BASE/api/products" -H 'Content-Type: application/json' \
  -d "{\"sku\":\"$SKU\",\"name\":\"Smoke test item\",\"category\":\"Other\",\"quantity\":5,\"reorder_level\":2,\"unit_price\":10}" \
  | sed -E 's/.*"id":([0-9]+).*/\1/')
pass "POST   /api/products            -> id $ID"

curl -fsS "$BASE/api/products/$ID" >/dev/null && pass "GET    /api/products/$ID"
curl -fsS -X PUT "$BASE/api/products/$ID" -H 'Content-Type: application/json' -d '{"unit_price": 12.5}' >/dev/null \
  && pass "PUT    /api/products/$ID"
curl -fsS -X POST "$BASE/api/products/$ID/adjust" -H 'Content-Type: application/json' \
  -d '{"change": -2, "reason": "sale", "note": "smoke test"}' >/dev/null && pass "POST   /api/products/$ID/adjust"
curl -fsS -X DELETE "$BASE/api/products/$ID" -o /dev/null && pass "DELETE /api/products/$ID"

echo "All checks passed."
