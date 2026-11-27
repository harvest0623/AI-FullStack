# Day03 - 数据加载 Loaders / 代码说明

本章代码位于 `Code/` 目录。文件加载与自定义 Loader 可离线运行；网页加载需联网（失败会自动降级）。

## 环境准备

```bash
pip install llama-index llama-index-readers-file llama-index-readers-web python-dotenv
# JSON 专用 reader（可选）
pip install llama-index-readers-json
```

> 需要在 `.env` 中配置 API Key 的场景不影响本章加载演示（加载本身不调用 LLM）。

## 文件说明

| 文件 | 说明 | 是否需联网 |
|------|------|-----------|
| `01_simple_reader.py` | SimpleDirectoryReader：基础加载 / 递归 recursive / 扩展名过滤 required_exts / metadata 输出，自动生成示例文档 | 否 |
| `02_file_readers.py` | 各格式 Reader：Markdown / CSV（SimpleDirectoryReader 自动识别），PDF / DOCX 专用 Reader（未安装/无文件则降级提示） | 否 |
| `03_web_reader.py` | WebPageReader（网页）/ StringReader（字符串）/ JSONReader（JSON） | 网页部分需联网 |
| `04_custom_loader.py` | 继承 BaseReader 实现 load_data() 的自定义 Loader，接入自定义"JSON/API"数据源 | 否 |

## 运行方式

```bash
python 01_simple_reader.py
python 02_file_readers.py
python 03_web_reader.py     # 联网体验网页加载
python 04_custom_loader.py
```

## 运行后生成的文件

- `data/readme.txt`、`data/docs_nested/nested.md`、`data/docs_md/note.md`（`01` 生成）
- `data/guide.md`、`data/employees.csv`（`02` 生成）
- `data/sample.json`（`03` 生成）
- `data/knowledge.json`（`04` 生成）