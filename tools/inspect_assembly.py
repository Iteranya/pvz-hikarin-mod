import dnfile

path = r"C:\Users\dev-01\Downloads\PvZ-Fusion-4.1-English-PC-Hikarin\MelonLoader\Il2CppAssemblies\Assembly-CSharp.dll"
pe = dnfile.dnPE(path)

def get_str(idx):
    try:
        return pe.net.mdtables.strings[idx]
    except Exception:
        return f"#{idx}"

types = {}
for t in pe.net.mdtables.TypeDef:
    name = get_str(t.TypeName)
    ns = get_str(t.TypeNamespace)
    types[t.row_id if hasattr(t, "row_id") else id(t)] = f"{ns}.{name}" if ns else name

# MethodDef rows: parent is via MethodDef -> TypeDef mapping is not direct in dnfile?
# dnfile: pe.net.mdtables.MethodDef each has ... use strings to guess owner by order:
# Simpler: print all method names containing keywords
keywords = ["level", "enter", "start", "load", "play"]
methods = []
for m in pe.net.mdtables.MethodDef:
    name = get_str(m.Name)
    if any(k in name.lower() for k in keywords):
        methods.append(name)

print("=== Types with Level/Custom/Board ===")
for t in pe.net.mdtables.TypeDef:
    name = get_str(t.TypeName)
    if any(k in name for k in ("Level", "Custom", "Board", "Scene")):
        print(get_str(t.TypeNamespace) + "." + name)

print("=== Methods matching keywords (unique, first 120) ===")
seen = []
for m in methods:
    if m not in seen:
        seen.append(m)
for m in seen[:120]:
    print(m)
print("total matching method rows:", len(methods))
