# zongce-filing · 综测填报 skill

把学院的**综合素质测评细则**、**个人加分项目清单**和一堆**佐证材料**，加工成两份可直接提交的成品：个人明细表 `xlsx` + 按填报顺序编号的佐证材料汇编 `docx`。

## 快速开始

```bash
# 0) 依赖
python3 -c "import openpyxl, docx, PIL, pymupdf; print('ok')"
pip3 install openpyxl python-docx pillow pymupdf
# macOS 处理扫描版 PDF（学籍/名册/秩序册）还需要：
pip3 install pyobjc-framework-Vision pyobjc-framework-Quartz

# 1) 盘点佐证材料
python3 scripts/scan_evidence.py <佐证材料目录> -o /tmp/evidence_preview --json /tmp/inventory.json

# 2) 扫描件定位（无文本层的 PDF）
python3 scripts/ocr_scanned_pdf.py 秩序册.pdf --keys <姓名> <编号> --out /tmp/ocr \
        --render-pages 62,75

# 3) 生成明细表
python3 scripts/build_detail_xlsx.py detail.json

# 4) 生成佐证汇编
python3 scripts/build_evidence_docx.py evidence.json
```

配置文件格式见 `scripts/build_detail_xlsx.py` 与 `scripts/build_evidence_docx.py` 的模块 docstring。

## 目录

```
SKILL.md                              工作流、输出约定、硬约束
references/scoring-cheatsheet.md      读细则时该抄下什么 + 定分六大坑
references/evidence-toolbox.md        PDF / 扫描件 OCR / 图片 / Word / 公示页 的取证方法
references/output-conventions.md      xlsx·docx 结构、用户偏好、提交前自检、踩坑表
scripts/scan_evidence.py              佐证目录盘点 + 压缩预览
scripts/ocr_scanned_pdf.py            扫描版 PDF 逐页 OCR + 关键词定位 + 命中页渲染
scripts/build_detail_xlsx.py          JSON → 明细表 xlsx（自动合并类别列）
scripts/build_evidence_docx.py        JSON → 佐证汇编 docx（编号 + 说明 + 图片）
```

## 边界

- 只读用户的原始材料，产物一律写新文件；
- 不伪造佐证；自制摘录图必须标注"据 <原文件名> 原文转录"；
- 归类、计次、累加这类有实质分歧的口径，**问用户**，不替他决定；
- 本 skill 内所有示例均使用 `<姓名>`、`<编号>`、`<项目名>` 占位，不含真实个人信息。
