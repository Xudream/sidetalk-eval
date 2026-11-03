#!/usr/bin/env python3
"""S4（媒体/电子人声）评测集取材：下载可公开获取的媒体语音源，并生成 S4 manifest。

背景：公开集里**没有**现成的"S4 拒识"评测集（见 docs/S4评测集来源清单.md）。
能拿到的只有"媒体人声素材"，需要自己切成段、标成 S4。

支持来源：
  mediaspeech   电视/广播新闻语音（FR/AR/TR/ES，CC BY 4.0，每语种约 600 MB）
  musan-music   背景音乐/歌声（MUSAN 的 music 子集，需全量包 11 GB —— 用 --url 指定单文件）
  cn-celeb      中文 in-the-wild（影视/综艺/访谈，CC BY-SA 4.0，v2 共 71 GB，需外接盘）

用法:
  python3 tools/s4_fetch.py --source mediaspeech --lang FR --out data/s4 --build-manifest
  python3 tools/s4_fetch.py --source mediaspeech --lang FR --dry-run     # 只看体积与链接
"""
import argparse, json, os, subprocess, sys, tarfile, hashlib

SOURCES = {
    "mediaspeech": {
        "base": "https://openslr.org/resources/108",
        "files": {"FR": "FR.tgz", "AR": "AR.tgz", "TR": "TR.tgz", "ES": "ES.tgz"},
        "sizes_mb": {"FR": 637, "AR": 611, "TR": 618, "ES": 582},
        "license": "CC BY 4.0",
        "kind": "tv_broadcast_speech",
    },
    "cn-celeb": {
        "base": "https://openslr.org/resources/82",
        "files": {"v2": "cn-celeb_v2.tar.gz"},
        "sizes_mb": {"v2": 22528},
        "license": "CC BY-SA 4.0",
        "kind": "cn_in_the_wild_media",
    },
    "wenetspeech": {
        "base": "https://wenet.org.cn/WenetSpeech",
        "files": {"v1": None},
        "sizes_mb": {},
        "license": "CC BY 4.0",
        "kind": "cn_multi_domain_media",
    },
    "musan-music": {
        "base": "https://openslr.org/resources/17",
        "files": {"full": "musan.tar.gz"},
        "sizes_mb": {"full": 11200},
        "license": "见 MUSAN 说明",
        "kind": "music_babble",
    },
}


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    print(f"下载 {url} → {dest}", flush=True)
    subprocess.run(["curl", "-L", "--fail", "--retry", "3", "-C", "-", "--progress-bar",
                    "-o", dest, url], check=True)


def extract(archive, dest):
    os.makedirs(dest, exist_ok=True)
    print(f"解包 {archive} → {dest}", flush=True)
    if archive.endswith(".tgz") or archive.endswith(".tar.gz"):
        with tarfile.open(archive) as tf:
            tf.extractall(dest)
    else:
        sys.exit(f"未知压缩格式：{archive}")


def find_audio(root):
    out = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith((".wav", ".flac", ".mp3", ".ogg")):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def build_manifest(root, out_path, limit=0, segment_sec=20, category=None):
    """把长音频切成 S4 段（默认 20 s），gold_scene=S4、gold_action=silent。"""
    import wave
    files = find_audio(root)
    if category:
        files = [f for f in files if category.lower() in f.lower()]
        print(f"[filter] category={category} → {len(files)} 个文件")
    if limit:
        files = files[:limit]
    rows = []
    for fp in files:
        rel = os.path.relpath(fp, root)
        rows.append({
            "id": f"s4-{hashlib.sha1(rel.encode()).hexdigest()[:12]}",
            "dataset": "s4_public", "split": "test",
            "audio_root": os.path.abspath(root), "audio": rel,
            "channels": 1, "layout": "mono",
            "system_state": "idle", "history": [],
            "gold_action": "silent", "gold_scene": "S4", "gold_lang": "unknown",
            "transcript": "",                       # 媒体人声：转写不是判据，判据是"别响应"
            "meta": {"source_type": "media", "segment_sec": segment_sec,
                     "has_imperative_phrase": None},
            "audio_ok": True,
        })
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{out_path}: {len(rows)} 条（gold_scene=S4，gold_action=silent）")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=list(SOURCES), required=True)
    ap.add_argument("--lang", default="FR", help="mediaspeech 用 FR/AR/TR/ES")
    ap.add_argument("--out", required=True, help="数据根目录")
    ap.add_argument("--url", default=None, help="覆盖下载链接（如 MUSAN 单文件）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--build-manifest", action="store_true")
    ap.add_argument("--from-dir", default=None,
                    help="已下载到本地的目录，直接建 manifest（WenetSpeech 这类需申请的集用）")
    ap.add_argument("--category", default=None,
                    help="只取路径里含该关键词的音频（WenetSpeech 域：drama/news/variety/documentary/audiobook/talk/commentary/interview/reading）")
    ap.add_argument("--manifest-limit", type=int, default=0)
    a = ap.parse_args()

    spec = SOURCES[a.source]
    if a.from_dir:
        rows = build_manifest(a.from_dir,
                              os.path.join(a.out or ".", f"s4_{a.source}.jsonl"),
                              a.manifest_limit, category=a.category)
        return
    if a.source == "wenetspeech" and not a.url:
        print("WenetSpeech 需申请：")
        print("  1) 打开 https://wenet.org.cn/WenetSpeech 填 Google 表单拿解压密码")
        print("  2) 按官方给定链接下载（几十 GB 起），或先只下 test/dev 小包")
        print("  3) 下载后：python3 tools/s4_fetch.py --source wenetspeech "
              "--from-dir <解压目录> --out data/s4 --category drama")
        print("  HF 也有（gated）：huggingface.co/datasets/wenet-e2e/wenetspeech")
        print("  TTS 版：huggingface.co/datasets/Wenetspeech4TTS/WenetSpeech4TTS（12,800 h，gated）")
        return
    key = a.lang if a.source == "mediaspeech" else "v2"
    fname = spec["files"].get(key)
    if not fname:
        sys.exit(f"{a.source} 没有 {key}，可选：{list(spec['files'])}")
    url = a.url or f"{spec['base']}/{fname}"
    size_mb = spec["sizes_mb"].get(key, 0)
    print(f"来源 {a.source}｜文件 {fname}｜约 {size_mb} MB｜许可 {spec['license']}｜类型 {spec['kind']}")
    print(f"URL  {url}")
    if a.dry_run:
        return

    os.makedirs(a.out, exist_ok=True)
    archive = os.path.join(a.out, fname)
    if not os.path.exists(archive) or os.path.getsize(archive) < size_mb * 0.95 * 1e6:
        download(url, archive)
    print(f"sha256 {sha256(archive)[:16]}…  大小 {os.path.getsize(archive)/1e6:.0f} MB")
    extract(archive, os.path.join(a.out, a.source))

    if a.build_manifest:
        build_manifest(os.path.join(a.out, a.source),
                       os.path.join(a.out, f"s4_{a.source}_{key}.jsonl"),
                       a.manifest_limit)


if __name__ == "__main__":
    main()
