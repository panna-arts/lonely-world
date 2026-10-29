#!/usr/bin/env bash
# 部署 GTM 落地页到 Meoo（项目: lonely-world GTM / https://yk5p80w5xvod.meoo.fun）
# 用法: bash GTM/deploy-meoo.sh
# 做四件事: 渲染 og-card.png → 组装 dist/ → meoo deploy → 线上自检
set -euo pipefail
cd "$(dirname "$0")/.."   # 仓库根目录

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MEOO="${MEOO_BIN:-$HOME/.local/bin/meoo}"
BASE="https://yk5p80w5xvod.meoo.fun"

[ -x "$CHROME" ] || { echo "✗ 未找到 Chrome，无法渲染 og-card"; exit 1; }
[ -x "$MEOO" ]   || { echo "✗ 未找到 meoo CLI（可用 MEOO_BIN=... 指定）"; exit 1; }
[ -f .env ] && grep -q MEOO_PROJECT_URL_ID .env || { echo "✗ 缺少 .env 中的 MEOO_PROJECT_URL_ID 绑定"; exit 1; }

echo "[1/4] 渲染 og-card.png / og-card-en.png（1200×630）…"
"$CHROME" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,630 --screenshot=GTM/og-card.png \
  --virtual-time-budget=10000 "file://$(pwd)/GTM/og-card.html" 2>/dev/null
"$CHROME" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1200,630 --screenshot=GTM/og-card-en.png \
  --virtual-time-budget=10000 "file://$(pwd)/GTM/og-card-en.html" 2>/dev/null

echo "[2/4] 组装 dist/ …"
mkdir -p dist
cp GTM/index.html     dist/index.html
cp GTM/en.html        dist/en.html         # 英文版（/en.html）
cp GTM/og-card.png    dist/og-card.png     # og:image 指向站点根路径，必须随页面一起上线
cp GTM/og-card-en.png dist/og-card-en.png  # 英文版 og:image

echo "[3/4] meoo deploy …"
"$MEOO" deploy --skip-build --skip-push --force

echo "[4/4] 线上自检 …"
# 注意: CDN 对 HTML 有约 1 分钟缓存，部署后立即检查会误报旧版；图片资产即时生效。
# 因此 HTML 检查带缓存穿透参数并做短重试。
check_html(){ # $1=url-fragment $2=grep-pattern
  for i in 1 2 3 4 5; do
    if curl -sf "$1?cb=$RANDOM$RANDOM" | grep -q "$2"; then return 0; fi
    sleep 12
  done
  return 1
}
FAIL=0
check_html "$BASE/" 'og:image'                          && echo "✓ og:image meta"       || { echo "✗ og:image meta 缺失"; FAIL=1; }
check_html "$BASE/" 'id="demo"'                         && echo "✓ 试玩 demo 区块"      || { echo "✗ demo 区块缺失"; FAIL=1; }
curl -sf -o /dev/null -w "✓ og-card.png HTTP %{http_code} (%{size_download}B)\n" "$BASE/og-card.png" || { echo "✗ og-card.png 404"; FAIL=1; }
check_html "$BASE/en.html" 'id="demo"'                  && echo "✓ en.html 试玩区块"    || { echo "✗ en.html 缺失 demo"; FAIL=1; }
curl -sf -o /dev/null -w "✓ og-card-en.png HTTP %{http_code} (%{size_download}B)\n" "$BASE/og-card-en.png" || { echo "✗ og-card-en.png 404"; FAIL=1; }

[ "$FAIL" -eq 0 ] && echo "全部通过: $BASE" || { echo "存在失败项，请检查"; exit 1; }
