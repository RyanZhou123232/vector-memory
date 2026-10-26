"""Render the actual HappyDB smoke-test output; no API calls or database writes."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def esc(value):
    return html.escape(str(value),quote=True)


def main():
    report=json.loads((ROOT/".reports"/"happydb_smoke.json").read_text(encoding="utf-8"))
    manifest=json.loads((ROOT/"dataset_manifest.json").read_text(encoding="utf-8"))
    parts=['''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>HappyDB · 迁移测试结果</title>
<style>body{font:15px/1.7 system-ui,"Microsoft YaHei",sans-serif;color:#20252b;background:white;margin:0}
main{max-width:1050px;margin:auto;padding:30px 24px 70px}h1{font-size:26px}h2{font-size:20px}
section{border-top:1px solid #dce2e8;padding:24px 0}details{border:1px solid #dce2e8;padding:12px 16px;border-radius:5px;margin:12px 0}
summary{cursor:pointer;font-weight:600}blockquote{border-left:3px solid #dce2e8;padding:8px 16px;margin:12px 0;background:#f5f7f9}
article{border-top:1px solid #dce2e8;padding:12px 0;scroll-margin-top:16px}article p{white-space:pre-wrap}
.caption{font-size:12px;color:#606b76}a{color:#205b91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f9;padding:12px;font-size:12px;max-height:60vh;overflow:auto}
.bad{color:#9b2424}.good{color:#246143}.flow{color:#606b76;border-block:1px solid #dce2e8;padding:12px 0}
</style></head><body><main><h1>HappyDB：新数据源迁移后的小测试</h1>''']
    parts.append(f'<p>当前数据库：<b>{manifest["stored_chunks"]} 条 HappyDB 记录</b>，来自 {manifest["anonymous_contributors"]} 位匿名贡献者的自述。</p>')
    parts.append('<p class="caption">原始来源：<a href="https://github.com/megagonlabs/HappyDB">Megagon Labs / HappyDB</a>。不把这些经历当成当前用户的朋友、身份或事件日期。</p>')
    parts.append('<p class="flow">问题 → DeepSeek 生成检索句 → Chroma 多次搜索 → 合并记录 → 综合回答 → 引用检查及模型审核</p>')
    parts.append('<h2>功能验证</h2><ul>')
    for key,value in report["checks"].items(): parts.append(f'<li>{esc(key)}：{esc(value)}</li>')
    parts.append('</ul><p class="caption">以下是少量实际问题的端到端时间与输出，不是总体准确率评测。</p>')
    for case in report["queries"]:
        key=case["case"]
        result=case.get("result",{})
        trace=case.get("trace",{})
        status=result.get("status","failed")
        parts.append(f'<section><h2>{esc(key)} · {esc(status)} · {case["elapsed_seconds"]:.2f} 秒</h2>')
        parts.append(f'<blockquote>{esc(case["question"])}</blockquote>')
        if case.get("error"):
            parts.append(f'<p class="bad">{esc(case["error"])}</p></section>')
            continue
        parts.append('<h3>实际回答</h3><p>'+esc(result.get("summary",""))+'</p>')
        for index,insight in enumerate(result.get("insights",[]),1):
            parts.append(f'<p><b>{index}. {esc(insight["point"])}</b></p>')
            for source in insight["sources"]:
                parts.append(f'<blockquote>{esc(source["quote"])} <a href="#{esc(key)}-{esc(source["id"])}">[{esc(source["id"])}]</a></blockquote>')
        parts.append(f'<p class="caption">检索次数：{trace.get("merge",{}).get("search_count",0)}；去重记录：{trace.get("merge",{}).get("unique_notes",0)}；模型调用：{len(trace.get("model_calls",[]))}。</p>')
        if result.get("evidence"):
            parts.append('<details><summary>回答引用的完整原文</summary>')
            for note in result["evidence"]:
                parts.append(f'<article id="{esc(key)}-{esc(note["id"])}"><b>[{esc(note["id"])}]</b><p>{esc(note["text"])}</p><p class="caption">{esc(json.dumps(note["metadata"],ensure_ascii=False))}</p></article>')
            parts.append('</details>')
        parts.append('<details><summary>实际检索句和全部命中记录</summary>')
        for search in trace.get("searches",[]):
            parts.append(f'<details><summary>检索 {search["index"]} · {len(search["hits"])} 条</summary><blockquote>{esc(search["query"])}</blockquote>')
            for hit in search["hits"]:
                parts.append(f'<article><div class="caption">#{hit["rank"]} [{esc(hit["id"])}] · distance {hit["distance"]:.5f}</div><p>{esc(hit["text"])}</p></article>')
            parts.append('</details>')
        parts.append('</details><details><summary>完整模型输入、返回和检查记录</summary><pre>')
        parts.append(esc(json.dumps(trace,ensure_ascii=False,indent=2)))
        parts.append('</pre></details></section>')
    parts.append('''<p class="caption">数据文件、密钥和数据库未发布；本报告仅显示本地真实测试结果。</p></main>
<script>document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');if(!a)return;var t=document.getElementById(a.getAttribute('href').slice(1));if(!t)return;for(var p=t;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}e.preventDefault();t.scrollIntoView({block:'start'});});</script></body></html>''')
    target=ROOT/".reports"/"happydb_test_report.html"
    target.write_text("".join(parts),encoding="utf-8")
    print(str(target))


if __name__=="__main__": main()
