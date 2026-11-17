# -*- coding: utf-8 -*-
"""
Day08 - 02 自建最小 Agent

复用 Day06 的循环 + 记忆（messages 里保留历史），形成可多步自主完成任务的
最小 Agent。离线可运行。

这里简化真实模型：用一个规则决策函数模拟『能按问答拆解』的行为，
用于示范循环+记忆的结构。
"""

import json

# 工具库
def get_weather(city):
    return {"北京": "晴 22°C", "上海": "小雨 30°C"}.get(city, "未知")


TOOLS = {"get_weather": get_weather}
MAX_ITER = 6


def decide(messages):
    """极简决策：模拟模型。首轮&&问天气→调工具；否则作答。"""
    has_tool_result = any(m["role"] == "tool" for m in messages)
    user_q = messages[0]["content"]
    if "天气" in user_q and not has_tool_result:
        city = "北京" if "北京" in user_q else "上海"
        return {"content": None, "tool_calls": [{
            "id": "c1", "type": "function",
            "function": {"name": "get_weather", "arguments": json.dumps({"city": city})},
        }]}
    return {"content": "据此稍等，我来帮你组织：" + (get_weather("北京") if "北京" in user_q else get_weather("上海"))}


def mini_agent(user_input):
    messages = [{"role": "user", "content": user_input}]
    print(f"  用户：『{user_input}』\n")
    for it in range(MAX_ITER):
        print(f"  —— 第 {it+1} 轮 ——")
        resp = decide(messages)
        if not resp.get("tool_calls"):
            print(f"  [Agent] 完成：『{resp['content']}』")
            return
        tc = resp["tool_calls"][0]
        name = tc["function"]["name"]
        args = json.loads(tc["function"]["arguments"])
        result = TOOLS[name](**args)
        print(f"  [执行] {name}{args} → {result}")
        messages.append({"role": "assistant", "tool_calls": resp["tool_calls"]})
        messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
    print("  ⚠ 已达最大迭代")


def main():
    print(">> 自建最小 Agent\n")
    mini_agent("上海现在天气怎么样？")
    print("\n  tips: 跟 Day06 的循环几乎一样，这里只是把它叫成了『Agent』，并保留记忆。")


if __name__ == "__main__":
    main()