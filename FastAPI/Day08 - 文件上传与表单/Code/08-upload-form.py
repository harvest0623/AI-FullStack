"""
Day08 练习：文件上传 UploadFile + 表单 Form
======================================
接收上传文件并读取内容, 同时接收表单字段, 用 TestClient 上传验证。

运行:
  python "Code/08-upload-form.py"
"""
from fastapi import FastAPI, UploadFile, Form
from fastapi.testclient import TestClient

app = FastAPI(title="上传与表单")

@app.post("/upload")
def upload(file: UploadFile, note: str = Form(...)):
    """接收文件 + 一个表单字段 note。"""
    content = file.file.read()                  # 同步接口直接读文件对象
    return {
        "filename": file.filename,
        "size": len(content),
        "first10": content[:10].decode("utf-8", errors="replace"),
        "note": note,
    }

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """表单登录示例(演示多个 Form 字段)。"""
    return {"ok": username == "admin" and password == "secret", "user": username}


client = TestClient(app)

print("1) 上传 txt 文件 + 表单字段")
r = client.post(
    "/upload",
    files={"file": ("报告.txt", "Hello FastAPI 上传".encode("utf-8"), "text/plain")},
    data={"note": "这是一份演示报告"},
)
body = r.json()
print(f"   status={r.status_code}")
print(f"   filename={body['filename']}  size={body['size']}")
print(f"   first10={body['first10']!r}  note={body['note']}")
assert body["filename"] == "报告.txt"
assert body["size"] == len("Hello FastAPI 上传".encode("utf-8"))
assert body["note"] == "这是一份演示报告"

print("2) 上传图片 PNG(二进制)")
r = client.post(
    "/upload",
    files={"file": ("头像.png", b"\x89PNG..." + bytes(range(10)), "image/png")},
    data={"note": "头像"},
)
print(f"   filename={r.json()['filename']}  size={r.json()['size']}")
assert r.json()["filename"] == "头像.png"

print("3) 表单登录(正确密码)")
r = client.post("/login", data={"username": "admin", "password": "secret"})
print(f"   {r.json()}")
assert r.json()["ok"] is True

print("4) 表单登录(错误密码)")
r = client.post("/login", data={"username": "admin", "password": "wrong"})
print(f"   {r.json()}")
assert r.json()["ok"] is False

print("\n全部通过 ✓  文件 + 表单字段 可同接口上传")