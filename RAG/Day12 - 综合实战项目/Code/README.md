# Day12 - 综合实战项目 · 代码目录

> 本目录文件均以 `python <文件名>.py` 直接运行。

| 文件 | 内容 | 需联网 |
|------|------|--------|
| `01_project_structure.py` | 生成 DataIQ 项目骨架 | 否 |
| `02_data_pipeline.py` | 加载→切块→嵌入→入库 | 是（可降级） |
| `03_retriever_engine.py` | 混合检索 + 重排 + 生成整合 | 是（可降级） |
| `04_full_service.py` | DataIQ 完整 FastAPI 服务 | 是（可降级） |

## 运行

```bash
# 1. 建骨架（生成 dataiq/ 目录）
python 01_project_structure.py

# 2. 数据管道 + 入库（生成 ./dataiq_index）
python 02_data_pipeline.py

# 3. 检索+生成引擎
python 03_retriever_engine.py

# 4. 启动完整服务
python 04_full_service.py
#    或 uvicorn 04_full_service:app --reload --port 8000
#    测试：POST /query {"question":"住宿报销","dept":"财务"}
```

> 配置 `OPENAI_API_KEY` 即走真实生成；否则服务降级返回"检索到的上下文"，全链路调用顺序仍可观察。

## 依赖

```bash
pip install fastapi uvicorn pydantic langchain-community faiss-cpu langchain-openai openai python-dotenv
```