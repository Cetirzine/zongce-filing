# 取证工具箱

佐证材料千奇百怪：手机照片、微信截图、公众号文章、学院公示 PDF、扫描版秩序册、Word 名单。下面是这次实操验证过的取法。

## 1. 路径与文件盘点

先 `ls -R` 列出佐证目录，注意三类文件：

- **图片**（`.jpg/.jpeg/.png/.heic`）：手机照常有 EXIF 旋转，必须先转正；
- **公示类 PDF**：学院下发的名单/考评结果，**既是证据也可能是口径校准器**（自述与公示不一致时以公示为准或写明差异）；
- **Word 名单/秩序册**：往往是"报名/检录"记录，不含名次。

```bash
python3 scripts/scan_evidence.py <佐证材料目录> -o /tmp/evidence_preview
```
输出清单（路径 / 尺寸 / 大小）与压缩预览图，便于快速目检。

## 2. 有文本层的 PDF

```bash
pdftotext -layout 文件.pdf /tmp/out.txt
```
`-layout` 保表格列位；再用关键词 grep 定位行。**注意**：带 `| head` 的管道在被拦时会丢失退出码，脚本化时把命令包到 `.py`/`.sh` 里跑更稳。

## 3. 无文本层的扫描版 PDF（关键场景）

判断：`pymupdf` 逐页 `get_text()` 全为空 → 扫描件。此时：

```bash
python3 scripts/ocr_scanned_pdf.py 秩序册.pdf --keys <姓名> <编号> 检录 <项目名> --render-pages 62,75
```

脚本用 macOS Vision（`pyobjc-framework-Vision`）以 120 dpi 逐页 OCR，关键词只做**定位**；命中页再用 150 dpi 渲染成图片当佐证。要点：

- 扫描件几十上百页很常见，**先 OCR 定位、再渲染命中页**，不要盲目翻页；
- OCR 结果可有错字（"掷"→"挣"），关键词要多给几个近义词；
- 早期版本只搜一个字也可能命中，命中后**必须人眼看图确认**；
- 无 macOS 时改用 `tesseract`（`brew install tesseract tesseract-lang`）。

## 4. 图片取用

```python
from PIL import Image, ImageOps
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
im.thumbnail((1600, 1600))          # 手机原图动辄 10-30MB，不压缩会让 docx 爆炸
im.save(dst, quality=82, optimize=True)
```
- 横图页宽 15cm、竖图 11cm（A4 页边距 2.2cm 时更好看）；
- 拼贴在 docx 前先目检：**照片里有没有本人**、场景是否是"当场"（很多细则要求"本人现场照/出场证明"）。

## 5. 公示页 / 官方名单当佐证

名单页不需要截图工具，直接渲染 PDF 页：
```python
pix = pymupdf.open(pdf)[page_no - 1].get_pixmap(dpi=150)   # A4 → 约 1240×1754
pix.save("out.jpg")
```
渲染后在 docx 说明里写清"第 N 页 / 序号 M"，方便审核人核对。

## 6. Word 材料（无 Word/LibreOffice 时）

- `qlmanage -t -s 2000 -o /tmp file.docx`：只能用 Quick Look 出**首页**缩略图，多页文档不够用；
- 想引用文档后半部分内容：用 `textutil -convert txt -stdout file.docx` 取全文，命中段落**自制"摘录图"**（PIL 绘制），并在图上与说明中标注"据 <原文件名> 原文转录"——不要伪装成原始截图；
- 有条件装 LibreOffice（`soffice --headless --convert-to pdf`）则优先转 PDF 后渲染原页。

## 7. 证据与条目的对应关系

- 一条佐证可以支撑多条项目（如一张检录表同时证明项目名与本人编号）；
- 一个项目可以配多张佐证（截图 + 公示页 + 现场照），按"越权威越靠前"；
- **无法佐证的项照样编号**，说明书里注明"（无需佐证材料）"，不要悄悄删掉用户明确要报的项。
