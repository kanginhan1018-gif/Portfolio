#!/bin/bash
# Preview a pptx as PNGs:  tools/pptx/preview.sh deck.pptx outprefix   (-> outprefix-01.png ...)
# Preview only: swaps Apple SD Gothic Neo for a CJK font and uses a throwaway LibreOffice profile,
# because LibreOffice ships no Korean font and cannot see ~/Library/Fonts/*.ttc on its own.
set -e
f="$1"; out="$2"
FONT="${PPT_PREVIEW_FONT:-$HOME/Library/Fonts/NotoSansCJK.ttc}"   # any CJK font file
PROFILE="${PPT_PROFILE:-${TMPDIR:-/tmp}/pptx-lo-profile}"
mkdir -p "$PROFILE/user/fonts"; [ -e "$PROFILE/user/fonts/$(basename "$FONT")" ] || cp "$FONT" "$PROFILE/user/fonts/"
tmp=$(mktemp -d); cp "$f" "$tmp/in.pptx"; cd "$tmp"; mkdir x; cd x; unzip -q ../in.pptx
grep -rl "Apple SD Gothic Neo" . | xargs sed -i '' 's/Apple SD Gothic Neo/Noto Sans CJK SC/g'
grep -rl 'typeface="' ppt/theme | xargs sed -i '' -E 's/(<a:(latin|ea|cs) typeface=")[^"]*"/\1Noto Sans CJK SC"/g'
zip -qr ../prev.pptx .; cd ..
soffice -env:UserInstallation=file://$PROFILE --headless --convert-to pdf prev.pptx >/dev/null 2>&1
pdftoppm -r "${PPT_DPI:-55}" -png prev.pdf "$out"
