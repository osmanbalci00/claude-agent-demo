#!/bin/bash
# Rebuild the Episode 3 demo folder from scratch (messy files + one deliberate
# duplicate fixture: messy/spreadsheets/budget.csv already exists, so the
# agent must rename the incoming messy/budget.csv instead of overwriting it.
# This is a demo fixture, disclosed in the narration and production notes.)
set -e
D=~/workspace/goals/side-gig-earning-1-000-a-month/files/youtube-episode-3/project/claude-agent-demo
rm -rf "$D"
mkdir -p "$D/messy"
cd "$D/messy"
cat > meeting-notes.txt <<'EOF'
Meeting notes — garden club, Nov 2026
- Order 20 more seed packets for spring
- Watering rota: Ana on Mondays, Ben on Thursdays
- Budget for the new shed: about 400 dollars
EOF
cat > shopping-list.txt <<'EOF'
Shopping list
- Milk, eggs, bread
- Coffee beans (dark roast)
- Batteries AA x8
EOF
cat > ideas.md <<'EOF'
# Weekend project ideas
- Build a birdhouse from scrap wood
- Learn to bake sourdough
- Organize the photo archive (one day...)
EOF
cat > budget.csv <<'EOF'
month,rent,groceries,transport,total
Oct,950,320,85,1355
Nov,950,290,90,1330
EOF
cat > expenses.csv <<'EOF'
date,item,amount
2026-11-01,coffee,4.50
2026-11-03,bookshop,18.99
2026-11-05,train ticket,12.40
EOF
cat > todo <<'EOF'
TODO (no file extension, on purpose)
- Call the plumber
- Renew library books
EOF
cat > hello.py <<'EOF'
# a tiny script that ended up in the wrong folder
print("hello from the messy folder")
EOF
python3 - <<'PYEOF'
from PIL import Image, ImageDraw
img = Image.new("RGB", (640, 480), (40, 90, 140))
d = ImageDraw.Draw(img)
d.ellipse([120, 80, 520, 400], fill=(242, 179, 61))
d.text((250, 220), "VACATION", fill=(255, 255, 255))
img.save("vacation.jpg")
img2 = Image.new("RGB", (400, 400), (245, 247, 250))
d2 = ImageDraw.Draw(img2)
d2.ellipse([60, 60, 340, 340], fill=(16, 42, 90))
d2.text((160, 190), "CAT", fill=(242, 179, 61))
img2.save("cat.png")
PYEOF
python3 - <<'PYEOF'
content = b"BT /F1 20 Tf 72 720 Td (Demo report - quarterly notes) Tj ET"
objs = []
objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")
objs.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
out = b"%PDF-1.4\n"
offsets = []
for i, o in enumerate(objs, 1):
    offsets.append(len(out))
    out += str(i).encode() + b" 0 obj\n" + o + b"\nendobj\n"
xref = len(out)
out += b"xref\n0 6\n0000000000 65535 f \n"
for off in offsets:
    out += ("%010d 00000 n \n" % off).encode()
out += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF"
open("report.pdf", "wb").write(out)
PYEOF
# Deliberate duplicate fixture (disclosed on camera): a file with the same
# name already sitting in the spreadsheets subfolder.
mkdir -p spreadsheets
cat > spreadsheets/budget.csv <<'EOF'
month,rent
Jan,900
(old budget from January — already here before the run)
EOF
ls -R "$D"
