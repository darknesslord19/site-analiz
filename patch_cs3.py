#!/usr/bin/env python3
"""
CS3 otomatik yama scripti.
  1) classes.dex -> smali
  2) Sabit domain string'ini DomainStore.read() çağrısıyla değiştirir
  3) Plugin.load() başına Hook.init(this, context) ekler (ayarlar popup'ı)
  4) smali -> dex, helper.dex'i classesN.dex olarak ekler, yeni .cs3 yazar

Gereken: java, tools/lib/*.jar (smali+baksmali), helper.dex (workflow üretir)

Kullanım:
  python patch_cs3.py Provider.cs3 --list
  python patch_cs3.py Provider.cs3 --domain https://eski.com -o Provider.patched.cs3
"""
import argparse, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

PKG = "Lcom/example/domainpatch"
STORE_CALL = f"invoke-static {{}}, {PKG}/DomainStore;->read()Ljava/lang/String;"
HOOK_CALL = (f"invoke-static/range {{p0 .. p1}}, {PKG}/Hook;->init("
             "Ljava/lang/Object;Landroid/content/Context;)V")
CONST_RE = re.compile(r'^(\s*)const-string(?:/jumbo)?\s+([vp]\d+),\s+"(https?://[^"]+)"\s*$')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Hata: {' '.join(map(str, cmd))}\n{r.stderr}")


def norm(u):
    return u.strip().rstrip("/").lower()


def list_candidates(smali_dir):
    seen = {}
    for f in smali_dir.rglob("*.smali"):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = CONST_RE.match(line)
            if m:
                seen.setdefault(m.group(3), set()).add(f.name)
    for url, files in sorted(seen.items()):
        print(f"{url}   <- {', '.join(sorted(files))[:80]}")


def patch_domain(smali_dir, domain):
    count = 0
    for f in smali_dir.rglob("*.smali"):
        lines = f.read_text(encoding="utf-8").split("\n")
        out, changed = [], False
        for line in lines:
            m = CONST_RE.match(line)
            if m and norm(m.group(3)) == norm(domain):
                out += [f"{m.group(1)}{STORE_CALL}", f"{m.group(1)}move-result-object {m.group(2)}"]
                changed = True
                count += 1
            else:
                out.append(line)
        if changed:
            f.write_text("\n".join(out), encoding="utf-8")
    return count


def patch_hook(smali_dir):
    for f in smali_dir.rglob("*.smali"):
        text = f.read_text(encoding="utf-8")
        if ".super Lcom/lagradost/cloudstream3/plugins/Plugin;" not in text:
            continue
        if HOOK_CALL in text:
            return True  # zaten yamalı
        lines, out, in_load, done = text.split("\n"), [], False, False
        for line in lines:
            out.append(line)
            if line.startswith(".method") and " load(Landroid/content/Context;)V" in line:
                in_load = True
            elif in_load and not done and re.match(r"\s*\.(locals|registers)\s+\d+", line):
                out.append(f"    {HOOK_CALL}")
                done = True
            elif line.startswith(".end method"):
                in_load = False
        if done:
            f.write_text("\n".join(out), encoding="utf-8")
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cs3")
    ap.add_argument("--domain", help="CS3 içinde sabit yazılı ESKİ domain")
    ap.add_argument("--list", action="store_true", help="bulunan URL'leri listele")
    ap.add_argument("--helper", default="helper.dex")
    ap.add_argument("--tools", default="tools")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    tools = Path(a.tools)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        x, sm = t / "x", t / "smali"
        with zipfile.ZipFile(a.cs3) as z:
            z.extractall(x)
        run(["java", "-cp", f"{tools}/lib/*", "org.jf.baksmali.Main", "d", x / "classes.dex", "-o", sm])

        if a.list:
            return list_candidates(sm)
        if not a.domain:
            sys.exit("--domain gerekli (önce --list ile bak)")

        n = patch_domain(sm, a.domain)
        if n == 0:
            sys.exit("Domain string'i bulunamadı. --list ile tam yazımı kontrol et.")
        if not patch_hook(sm):
            sys.exit("Plugin.load() bulunamadı; popup hook'u eklenemedi.")

        run(["java", "-cp", f"{tools}/lib/*", "org.jf.smali.Main", "a", sm, "-o", x / "classes.dex"])
        i = 2
        while (x / f"classes{i}.dex").exists():
            i += 1
        shutil.copy(a.helper, x / f"classes{i}.dex")

        out = Path(a.out or Path(a.cs3).with_suffix(".patched.cs3"))
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(x.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(x).as_posix())
        print(f"Tamam: {n} domain değiştirildi, popup hook eklendi -> {out}")


if __name__ == "__main__":
    main()
