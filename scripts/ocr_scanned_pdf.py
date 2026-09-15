#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描版（无文本层）PDF 逐页 OCR + 关键词定位 + 命中页渲染。

用法:
    python3 ocr_scanned_pdf.py 秩序册.pdf --keys <姓名> <编号> 检录 --out /tmp/ocr_out
    python3 ocr_scanned_pdf.py 秩序册.pdf --pages 62,75 --render-pages 62,75 --out /tmp/ocr_out

依赖:
    pymupdf            （渲染 + 文本层探测）
    macOS OCR 后端     pip3 install pyobjc-framework-Vision pyobjc-framework-Quartz
    非 macOS 环境      brew install tesseract tesseract-lang（脚本自动回退）

输出:
    <out>/ocr_pages.txt   每页 OCR 文本
    <out>/hits.md         关键词命中页与上下文
    <out>/page062.jpg ... --render-pages 指定页的 150dpi 渲染图（可直接做佐证）
"""
from __future__ import annotations

import argparse
import os
import sys

import pymupdf


def backend_macos():
    try:
        import Vision
        import Quartz
        from Foundation import NSData
    except ImportError:
        return None
    level = Vision.VNRequestTextRecognitionLevelAccurate

    def run(png_bytes):
        data = NSData.dataWithBytes_length_(png_bytes, len(png_bytes))
        src = Quartz.CGImageSourceCreateWithData(data, None)
        cg = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLanguages_(["zh-Hans", "en-US"])
        req.setRecognitionLevel_(level)
        req.setUsesLanguageCorrection_(True)
        Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg, None).performRequests_error_([req], None)
        out = []
        for obs in (req.results() or []):
            cand = obs.topCandidates_(1)
            if cand and len(cand):
                out.append(cand[0].string())
        return "\n".join(out)

    return run


def backend_tesseract():
    try:
        import subprocess
        import tempfile

        from PIL import Image  # noqa: F401
    except ImportError:
        return None

    def run(png_bytes):
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_bytes)
            tmp = f.name
        try:
            r = subprocess.run(["tesseract", tmp, "stdout", "-l", "chi_sim+eng"],
                               capture_output=True, text=True)
            return r.stdout
        finally:
            os.unlink(tmp)

    return run


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--keys", nargs="*", default=[], help="定位关键词（可多个，命中任一即记录）")
    ap.add_argument("--pages", default=None, help="只 OCR 这些页，如 62,75（默认全部）")
    ap.add_argument("--render-pages", default=None, help="额外渲染这些页为 jpg，如 62,75")
    ap.add_argument("--out", default="./ocr_out")
    ap.add_argument("--ocr-dpi", type=int, default=120)
    ap.add_argument("--render-dpi", type=int, default=150)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    doc = pymupdf.open(args.pdf)
    total = doc.page_count

    has_text = any(doc[i].get_text().strip() for i in range(min(total, 8)))
    if has_text:
        print("提示：前 8 页存在文本层，先用 `pdftotext -layout` 更省事；仍继续 OCR。", file=sys.stderr)

    ocr = backend_macos() or backend_tesseract()
    if ocr is None:
        print("缺少 OCR 后端：macOS 请 pip3 install pyobjc-framework-Vision pyobjc-framework-Quartz；"
              "其他平台请安装 tesseract。", file=sys.stderr)
        return 2

    pages = range(1, total + 1)
    if args.pages:
        pages = [int(p) for p in args.pages.split(",") if p.strip()]

    txt_path = os.path.join(args.out, "ocr_pages.txt")
    hits = []
    with open(txt_path, "w", encoding="utf-8") as f:
        for n in pages:
            page = doc[n - 1]
            pix = page.get_pixmap(dpi=args.ocr_dpi)
            text = ocr(pix.tobytes("png"))
            f.write(f"===== page {n}\n{text}\n\n")
            f.flush()
            hit = [k for k in args.keys if k and k in text]
            print(f"page {n}: {len(text)} chars {hit or ''}", flush=True)
            if hit:
                hits.append((n, hit, text))
    print(f"\nOCR 文本 -> {txt_path}")

    if args.keys:
        md = os.path.join(args.out, "hits.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write(f"# 关键词命中：{', '.join(args.keys)}\n\n")
            for n, hit, text in hits:
                f.write(f"## page {n}  hits={hit}\n\n{text}\n\n")
        print(f"命中 {len(hits)} 页 -> {md}")
        print("命中页：" + ", ".join(str(n) for n, _, _ in hits) if hits else "命中页：无")

    if args.render_pages:
        for p in [int(x) for x in args.render_pages.split(",") if x.strip()]:
            pix = doc[p - 1].get_pixmap(dpi=args.render_dpi)
            dst = os.path.join(args.out, f"page{p:03d}.jpg")
            pix.save(dst)
            print(f"render -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
