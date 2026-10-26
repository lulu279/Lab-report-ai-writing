"""Optional AI narrative draft. Never used for numerical calculation."""
import os
from pathlib import Path


def generate_discussion(results: dict, config, knowledge: Path, model: str | None) -> str:
    if not model:
        raise ValueError("Model ID is required for AI mode")
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")):
        raise ValueError("AI_API_KEY or OPENAI_API_KEY is unset: no AI writing was run")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("AI mode requires optional 'openai' package") from exc
    import json
    rules = knowledge.read_text(encoding="utf-8")[:7000]
    values = [{k:v for k,v in ev.items() if k not in {"method"}} for ev in results["events"]]
    prompt = (
        "你是科研文档草稿助手。你只能根据给定的已计算事件和校验结果撰写一段中文分析草稿。"
        "不得补造 Tg、原始数据、实验条件、引用或未经过验证的机理。"
        "应明确区分现象、可能原因与局限。回复纯文本，不要带标题、表格或参考文献。"
        "不应宣称这一文本通过科学审核；不要给出任何与下述事件不一致的新数值。\n"
        "个人风格（只用于语言格式，绝非实验数据）：\n"+rules+"\n"
        "事件数据：\n"+json.dumps(values,ensure_ascii=False)+"\n"
        "数值质量：\n"+json.dumps(results["validation"],ensure_ascii=False)
    )
    opts={"api_key":os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY"), "timeout":45.0}
    base=os.getenv("AI_BASE_URL")
    if base:
        if not (base.startswith("https://") or base.startswith("http://localhost:") or base.startswith("http://127.0.0.1:")):
            raise ValueError("AI_BASE_URL must be HTTPS or localhost")
        opts["base_url"]=base
    client = OpenAI(**opts)
    response = client.chat.completions.create(model=model,messages=[{"role":"user","content":prompt}])
    ans = response.choices[0].message.content
    if not ans or not ans.strip():
        raise RuntimeError("AI API returned empty discussion")
    return ans.strip()
