#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "🔑 激活虚拟环境..."
source mscript-env/bin/activate

echo "▶ 运行 MScript.py"
python MScript.py

echo "🚪 程序结束，退出虚拟环境"
deactivate