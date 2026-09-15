#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描佐证材料目录：清单 + 压缩预览图。

用法:
    python3 scan_evidence.py <佐证材料目录> [-o 预览输出目录] [--max 1600] [--json out.json]

输出:
    - stdout: markdown 清单（路径 / 类型 / 尺寸 / 大小）
    - 预览目录: 每张图片一个 EXIF 转正后的压缩 jpg
"""
from __future__ import annotations

import argparse
import json
import os
import sys

IMG_EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}
DOC_EXT = {".pdf", ".docx", ".doc", ".xlsx", ".rtf", ".txt", ".md"}


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}GB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="佐证材料根目录")
    ap.add_argument("-o", "--out", default=None, help="预览图输出目录")
    ap.add_argument("--max", type=int, default=1600, help="预览图最长边像素（默认 1600）")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--json", default=None, help="同时输出清单 JSON 的路径")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("需要 Pillow: pip3 install pillow", file=sys.stderr)
        return 2

    if args.out:
        os.makedirs(args.out, exist_ok=True)

    records = []
    print(f"# 佐证清单：{root}\n")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            path = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            size = os.path.getsize(path)
            rel = os.path.relpath(path, root)
            rec = {"path": path, "rel": rel, "ext": ext, "bytes": size}
            if ext in IMG_EXT:
                try:
                    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
                    rec["size"] = list(im.size)
                    if args.out:
                        dst = os.path.join(args.out, rel.replace(os.sep, "__"))
                        dst = os.path.splitext(dst)[0] + ".jpg"
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        prev = im.copy()
                        prev.thumbnail((args.max, args.max))
                        prev.save(dst, quality=args.quality, optimize=True)
                        rec["preview"] = dst
                    print(f"- [image] {rel}  {im.size[0]}x{im.size[1]}  {human(size)}")
                except Exception as e:  # noqa: BLE001
                    rec["error"] = str(e)
                    print(f"- [image?] {rel}  读取失败: {e}")
            elif ext in DOC_EXT:
                rec["size"] = None
                print(f"- [{ext.lstrip('.')}] {rel}  {human(size)}")
            else:
                print(f"- [other] {rel}  {human(size)}")
            records.append(rec)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"\nJSON -> {args.json}")
    print(f"\n共 {len(records)} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
