import re, pathlib, collections

D = pathlib.Path(r"c:\Users\selsherb\NIZAM\.kiro\specs\hermes-governed-workflows")
req = (D / "requirements.md").read_text(encoding="utf-8")
tasks = (D / "tasks.md").read_text(encoding="utf-8")
chk = (D / "acceptance-checklist.md").read_text(encoding="utf-8")
des = (D / "design.md").read_text(encoding="utf-8")

# ---- 1. defined criteria N.M from requirements.md ----
defined = set()
cur = None
for line in req.splitlines():
    m = re.match(r"^##\s+Requirement\s+(\d+):", line)
    if m:
        cur = int(m.group(1))
        continue
    if cur is not None:
        m2 = re.match(r"^(\d+)([a-d]?)\.\s+\S", line)
        if m2:
            defined.add(f"{cur}.{m2.group(1)}{m2.group(2)}")
print("requirements defined:", len(defined))
reqnums = sorted({int(c.split('.')[0]) for c in defined})
print("requirement numbers:", reqnums)
missing_reqs = [n for n in range(1, 30) if n not in reqnums]
print("requirement numbers with no criteria parsed:", missing_reqs)

# ---- 2. cited criteria in tasks.md ----
cited_tasks = set()
for m in re.finditer(r"_Requirements:\s*([^_]+)_", tasks):
    for tok in re.split(r"[,\s]+", m.group(1)):
        tok = tok.strip().rstrip('.').strip()
        if re.fullmatch(r"\d+\.\d+[a-d]?", tok):
            cited_tasks.add(tok)
print("\ntasks cited criteria:", len(cited_tasks))
print("cited but NOT defined:", sorted(cited_tasks - defined, key=lambda s: (int(s.split('.')[0]), s)))

# requirement-level coverage: does every requirement 1..29 appear in some task citation or coverage map?
covered = {int(c.split('.')[0]) for c in cited_tasks}
print("requirements with zero task criterion citation:", [n for n in range(1, 30) if n not in covered])

# ---- 3. checklist Req references ----
cited_chk = set()
for m in re.finditer(r"_Requirements:\s*([^_]+)_", chk):
    for tok in re.split(r"[,\s]+", m.group(1)):
        tok = tok.strip().rstrip('.')
        if re.fullmatch(r"\d+\.\d+[a-d]?", tok):
            cited_chk.add(tok)
# table Req column: last cell of a table row
for line in chk.splitlines():
    if line.strip().startswith("|") and line.count("|") >= 3:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        last = cells[-1]
        for tok in re.split(r"[,\s]+", last.replace("–", "-")):
            tok = tok.strip()
            m = re.fullmatch(r"(\d+)\.(\d+[a-d]?)-(\d+[a-d]?)", tok)
            if m:
                cited_chk.add(f"{m.group(1)}.{m.group(2)}")
                cited_chk.add(f"{m.group(1)}.{m.group(3)}")
            elif re.fullmatch(r"\d+\.\d+[a-d]?", tok):
                cited_chk.add(tok)
print("\nchecklist cited criteria:", len(cited_chk))
print("checklist cited but NOT defined:", sorted(cited_chk - defined, key=lambda s: (int(s.split('.')[0]), s)))

# ---- 4. tasks without a _Requirements_ citation ----
print("\n--- leaf sub-tasks lacking _Requirements: ---")
lines = tasks.splitlines()
top = leaf = 0
cur_task = None
buf = []
def flush(name, body):
    if name and not any("_Requirements:" in b for b in body):
        print("  NO CITATION:", name)
for i, line in enumerate(lines):
    m = re.match(r"^\s*-\s*\[\s*\]\*?\s*(\d+\.\d+)\s+(.*)", line)
    m_top = re.match(r"^-\s*\[\s*\]\s*(\d+)\.\s+(.*)", line)
    if m:
        flush(cur_task, buf); cur_task = m.group(1) + " " + m.group(2)[:60]; buf = []; leaf += 1
    elif m_top:
        flush(cur_task, buf); cur_task = m_top.group(1) + ". " + m_top.group(2)[:60]; buf = []; top += 1
    else:
        buf.append(line)
flush(cur_task, buf)
print(f"top-level tasks: {top}, leaf sub-tasks: {leaf}")

# ---- 5. AC-Ix-n identifiers across files ----
def acs(t):
    return collections.Counter(re.findall(r"AC-I\d+-\d+[a-z]?", t))
for name, t in (("design", des), ("requirements", req), ("tasks", tasks), ("checklist", chk)):
    print(name, "ACs:", sorted(acs(t).keys(), key=lambda s: (s.split('-')[1], int(re.sub(r'\D','',s.split('-')[2])), s)))
