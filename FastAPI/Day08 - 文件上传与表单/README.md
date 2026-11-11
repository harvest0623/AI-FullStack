# Day08 - 文件上传与表单

> 日常的 Web 服务常要处理**文件**（上传头像、导入 Excel）和**表单**（登录、注册）。
> 本讲使用 FastAPI 的 `UploadFile` 与 `Form`，讲解 multipart 文件上传与表单参数。

## 本讲目标

1. 用 `UploadFile` 接收上传文件，读取其内容与文件名、大小。
2. 用 `Form(...)` 接收表单字段（非 JSON 的键值数据）。
3. 演示"文件 + 表单字段"同接口上传的场景。
4. 用 TestClient 以 `files=` / `data=` 发起上传请求验证。

## 核心概念

| 概念 | 说明 |
|------|------|
| `UploadFile` | 接收上传的文件对象 |
| `.filename` | 原始文件名 |
| `await file.read()` | 读取文件全部字节 |
| `Form(...)` | 表单字段参数 |
| `files=` / `data=` | TestClient 里传文件 / 传表单字段的方式 |

## 上传接口

```python
from fastapi import UploadFile

@app.post("/upload")
def upload(file: UploadFile, note: str = Form(...)):
    content = file.file.read()          # 读取字节(Python 同步接口里直接读)
    return {
        "filename": file.filename,
        "size": len(content),
        "note": note,
    }
```

> 进阶提示：接口函数用 `async def` 时可 `await file.read()`；普通 `def` 里用 `file.file.read()`。
> 本讲都用同步 `def`（FastAPI 会放到线程池执行），代码更直白。

## TestClient 上传

```python
r = client.post("/upload",
                files={"file": ("数据.txt", b"hello world", "text/plain")},
                data={"note": "备注文字"})
```

## 运行

```bash
python "Code/08-upload-form.py"
```

## 你要体会的

- 上传用的编码叫 **multipart/form-data**，与 JSON 不同，用于二进制与表单。
- `UploadFile` 让你拿到文件名和内容，落地到磁盘（或云存储）由你决定。
- 文件 + 表单字段常一起出现（如"头像"+"昵称"）——`files` 与 `data` 可同时传。