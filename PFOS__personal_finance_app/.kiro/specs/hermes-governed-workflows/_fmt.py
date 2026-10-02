import pathlib, re, sys

p = pathlib.Path(r"c:\Users\selsherb\NIZAM\.kiro\specs\hermes-governed-workflows\requirements.md")
src = p.read_text(encoding="utf-8")
lines = src.split("\n")
out = []
changed_req = 0
changed_group = 0
for ln in lines:
    if re.match(r"^## Requirement \d+: ", ln):
        out.append("#" + ln)
        changed_req += 1
    elif re.match(r"^# Group [BCD] ", ln):
        out.append("##" + ln)
        changed_group += 1
    else:
        out.append(ln)
p.write_text("\n".join(out), encoding="utf-8")
print("requirement headings demoted:", changed_req)
print("group headings demoted:", changed_group)
