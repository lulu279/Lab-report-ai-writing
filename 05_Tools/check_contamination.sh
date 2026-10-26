#!/bin/sh
# 检查新报告中是否误用了旧范例的高特征数值。
#
# 用法：
#   sh 05_Tools/check_contamination.sh report.docx
#   sh 05_Tools/check_contamination.sh report.md --strict
#
# 退出码：
#   0 = 没有命中（或非 strict 模式）
#   1 = 有命中且 --strict
#   2 = 用法/文件错误
#
# 说明：命中不等于错误。若新实验确实得到相同数值，或复用了同一份原始数据，
# 请在交付说明里写明原因；否则视为污染，必须回到本次 DATA 重算。

set -u
FILE="${1:-}"
MODE="${2:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "usage: sh $0 <report.docx|report.md> [--strict]" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LIST="$SCRIPT_DIR/contamination_list.txt"
[ -f "$LIST" ] || { echo "missing list: $LIST" >&2; exit 2; }

TMP=$(mktemp 2>/dev/null || echo "/tmp/contam.$$")
trap 'rm -f "$TMP"' EXIT HUP INT TERM

case "$FILE" in
  *.docx)
    if command -v unzip >/dev/null 2>&1; then
      unzip -p "$FILE" word/document.xml | sed -e 's/<[^>]*>//g' > "$TMP"
    else
      echo "need unzip to read DOCX" >&2
      exit 2
    fi
    ;;
  *)
    cat "$FILE" > "$TMP"
    ;;
esac

found=0
while IFS='|' read -r value note; do
  case "$value" in
    ''|\#*) continue ;;
  esac
  if grep -Fq -- "$value" "$TMP"; then
    echo "MATCH: $value    <- $note"
    found=1
  fi
done < "$LIST"

if [ "$found" -eq 0 ]; then
  echo "OK: no known exemplar values found in $FILE"
  exit 0
fi

echo
echo "请逐条确认：这些数值是否来自本次 DATA？"
echo "- 若否：删除并重算。"
echo "- 若是同一次实验/同一份数据：在交付说明中写明原因。"
if [ "$MODE" = "--strict" ]; then
  exit 1
fi
exit 0
