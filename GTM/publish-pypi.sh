#!/usr/bin/env bash
# 构建 lonely-world 并发布到 PyPI
# 用法: bash GTM/publish-pypi.sh pypi-<你的API token>
# 前提: pyproject.toml 中的 version 高于 PyPI 上已有版本（首publish无此问题）
set -euo pipefail
cd "$(dirname "$0")/.."   # 仓库根目录

TOKEN="${1:?用法: bash GTM/pypi-publish.sh pypi-<token>  （token 见 https://pypi.org/manage/account/token/）}"

echo "[1/4] 安装构建工具 …"
python3 -m pip install --quiet --upgrade build twine

echo "[2/4] 构建 sdist + wheel → local/pypi-dist/ …"
# 注意: 不能用默认的 dist/ 目录——那是 meoo 静态部署的产物目录，会互相污染
rm -rf local/pypi-dist
python3 -m build --outdir local/pypi-dist

echo "[3/4] twine check …"
python3 -m twine check local/pypi-dist/*

echo "[4/4] 上传到 PyPI …"
python3 -m twine upload --non-interactive \
  --repository pypi -u __token__ -p "$TOKEN" \
  local/pypi-dist/*

echo "完成。验证安装:"
echo "  pip index versions lonely-world   或访问 https://pypi.org/project/lonely-world/"
echo "  pip install lonely-world && lonely-world --version"
