#!/usr/bin/env python3
"""把评测实际用到的音频打包（只打清单引用到的文件，不含整份数据集）。

输出：
  <out>/<dataset>.tar.gz      每个数据集一个包，内部路径为 <dataset>/<相对路径>
  <out>/SHA256SUMS            每个包的 sha256 + 字节数
  <out>/pack_manifest.json    包内文件清单（相对路径 → 字节数）

用法:
  python3 package_audio.py --manifests manifests --out ~/.hermes/workspace/ruler1/pack
  python3 package_audio.py --manifests manifests --out ... --datasets chorus,wearvox
"""
import argparse, glob, hashlib, json, os, tarfile, time
from collections import defaultdict


def collect(manifests_dir):
    """返回 {dataset: [(audio_root, rel_audio), ...]}（去重，保持稳定顺序）"""
    per = defaultdict(set)
    for f in sorted(glob.glob(os.path.join(manifests_dir, "*.jsonl"))):
        if os.path.basename(f).startswith("mini"):
            continue
        for line in open(f, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            root, rel = r.get("audio_root"), r.get("audio")
            if root and rel:
                per[r.get("dataset", "na")].add((root, rel))
    return {k: sorted(v) for k, v in per.items()}


def sha256_file(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", default="manifests")
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", default="", help="逗号分隔，默认全部")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    per = collect(a.manifests)
    want = [d.strip() for d in a.datasets.split(",") if d.strip()] or sorted(per)

    sums, index = [], {}
    for ds in want:
        files = per.get(ds)
        if not files:
            print(f"[skip] {ds} 无清单记录", flush=True)
            continue
        out = os.path.join(a.out, f"{ds}.tar.gz")
        t0, n, missing = time.time(), 0, []
        with tarfile.open(out, "w:gz", compresslevel=6) as tf:
            for root, rel in files:
                src = os.path.join(root, rel)
                if not os.path.exists(src):
                    missing.append(rel)
                    continue
                tf.add(src, arcname=f"{ds}/{rel}")
                n += 1
        size = os.path.getsize(out)
        digest = sha256_file(out)
        sums.append(f"{digest}  {ds}.tar.gz")
        index[ds] = {"files": n, "bytes": size, "sha256": digest, "missing": missing}
        print(f"[{ds}] {n} 个文件 → {out}  {size/1e6:.0f} MB  sha256={digest[:16]}…  "
              f"用时 {time.time()-t0:.0f}s" + (f"  缺 {len(missing)}" if missing else ""), flush=True)

    open(os.path.join(a.out, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
    json.dump(index, open(os.path.join(a.out, "pack_manifest.json"), "w"), ensure_ascii=False, indent=2)
    total = sum(v["bytes"] for v in index.values())
    print(f"合计 {total/1e9:.2f} GB → {a.out}", flush=True)


if __name__ == "__main__":
    main()
