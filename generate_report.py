"""Generate an escaped, offline report from existing JMH measurements."""
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def esc(value):
    return html.escape(str(value), quote=True)

def number(value):
    return f"{value:,.3f}" if isinstance(value, (int, float)) and math.isfinite(value) else "—"

LIBRARY_NAMES = {"rust-kmp": "mermaid-rust-kmp", "native": "mermaid-native · JVM 适配", "lugf": "lugf027 / mermaid", "cmp": "CMP Mermaid", "diagram": "huarangmeng / diagram"}
CASE_NAMES = {"simple_flowchart": ("简单流程图", "4 节点 · 3 条连线"), "complex_flowchart": ("复杂流程图", "11 节点 · 13 条连线 · 2 个子图"), "sequence_diagram": ("时序图", "3 位参与者 · 8 条消息")}


def render_tables(rows):
    sections = []
    stages = [("svg", "端到端 SVG", "解析 + 布局 + SVG 序列化"), ("parse", "解析", "Mermaid 源码 → 模型；不含布局"), ("scene", "场景生成", "解析 + 布局 → 场景；不含 Compose 绘制")]
    for stage, title, description in stages:
        chosen = [r for r in rows if r["params"]["operation"].endswith(":" + stage)]
        if not chosen:
            continue
        cards, parts = [], []
        for case, (case_title, subtitle) in CASE_NAMES.items():
            cells = sorted([r for r in chosen if r["params"]["caseName"] == case], key=lambda r: r["primaryMetric"]["score"])
            if not cells:
                continue
            maximum = max(r["primaryMetric"]["score"] for r in cells) or 1
            minimum = min(r["primaryMetric"]["score"] for r in cells)
            bars = []
            for row in cells:
                metric = row["primaryMetric"]
                library = row["params"]["operation"].split(":")[0]
                name = LIBRARY_NAMES.get(library, library)
                interval = metric.get("scoreConfidence", [None, None])
                allocation = row.get("secondaryMetrics", {}).get("gc.alloc.rate.norm", {}).get("score")
                sample = f'<a href="results/samples/{esc(library)}-{esc(case)}.svg">查看 SVG ↗</a>' if stage == "svg" else ""
                relative = ("本组耗时最低" if metric["score"] == minimum else f'耗时 {metric["score"] / minimum:.2f}×') if len(cells) > 1 and minimum > 0 else "单库测量"
                color = {"rust-kmp": "#bd614c", "native": "#317369", "lugf": "#6372c4", "cmp": "#b27936", "diagram": "#5386a8"}.get(library, "#6372c4")
                display_value, display_unit = (f"{metric["score"] / 1000:,.2f}", "ms") if metric["score"] >= 1000 else (f"{metric["score"]:,.2f}", "µs")
                bars.append(f'<div class="chart-row"><div class="chart-label"><span class="library"><i style="background:{color}"></i>{esc(name)}</span><strong>{display_value}<small> {display_unit}</small></strong></div><div class="track"><div class="fill" style="width:{metric["score"] / maximum * 100:.2f}%;background:{color}"></div></div><div class="chart-meta"><span>{relative}</span>{sample}</div></div>')
                parts.append(f'<tr><td>{case_title}</td><td>{esc(name)}</td><td>{number(metric["score"])} ± {number(metric.get("scoreError"))}</td><td>[{number(interval[0])}, {number(interval[1])}]</td><td>{number(allocation)}</td></tr>')
            note = '<p class="missing">diagram：此输入的 subgraph 解析失败，未计时。</p>' if stage == "parse" and case == "complex_flowchart" else ''
            cards.append(f'<article class="chart-card"><h3>{case_title}</h3><p class="case-caption">{subtitle}</p>{"".join(bars)}{note}</article>')
        sections.append(f'<section id="{stage}"><div class="section-heading"><div><h2>{title}</h2><p>{description}</p></div><span class="unit">耗时 / 次 · 越短越快</span></div><div class="chart-grid">{"".join(cards)}</div><p class="scale-note">每张卡片单独缩放；倍数以同图、同阶段的最低平均耗时为基准。差异不代表画质或兼容性。</p><details class="data-details"><summary>展开精确数值、置信区间与内存分配</summary><div class="table-scroll"><table><thead><tr><th>输入</th><th>库</th><th>平均耗时 ± 误差 (µs/op)</th><th>99.9% 置信区间</th><th>JVM 分配 (B/op)</th></tr></thead><tbody>{"".join(parts)}</tbody></table></div></details></section>')
    return "".join(sections)

def generate(root=ROOT):
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    rows = read("results/jmh.json")
    environment = read("results/environment.json")
    preflight = read("results/preflight.json")
    discovery = read("discovery.json")
    settings = environment["settings"]
    pre = []
    for row in preflight + environment.get("failures", []):
        status = row.get("status", "benchmark failed")
        pre.append(f'<tr><td>{esc(row["operation"])}</td><td>{esc(row["caseName"])}</td><td class="{ "failed" if status != "ok" else "" }">{esc(status)}</td><td>{esc(row.get("error", ""))}</td></tr>')
    libraries = []
    excluded = []
    for candidate in discovery["candidates"]:
        link = f'<a href="{esc(candidate["repository"])}">{esc(candidate["id"])}</a>'
        if candidate["status"] == "measured":
            libraries.append(f'<tr><td>{link}</td><td><code>{esc(candidate["commit"])}</code></td><td>{esc(candidate["notes"])}</td></tr>')
        else:
            excluded.append(f'<p>{link}: {esc(candidate["notes"])}</p>')
    toolchain = environment.get("toolchain", {})
    toolchain_note = f'<br>Kotlin {esc(toolchain.get("kotlin", "—"))} · coroutines {esc(toolchain.get("coroutines", "—"))}' if toolchain else ''
    replacements = {
        "__PROFILE__": esc(environment["profile"]),
        "__SUMMARY__": f'{len(rows)} 项成功测量 · {sum(r.get("status") != "ok" for r in preflight)} 项前置检查失败 · {len({r["params"]["operation"].split(":")[0] for r in rows})} 个库',
        "__ENVIRONMENT__": f'<p>{esc(environment["os"])} · {esc(environment["architecture"])}<br>{esc(environment["cpu"])}<br>{esc(environment["java"].splitlines()[0])}{toolchain_note}<br>UTC: {esc(environment["started_utc"])} → {esc(environment.get("finished_utc", "running"))}<br>{len(rows)} 个成功测量</p>',
        "__METHOD__": f'{settings["forks"]} 个 JVM fork；每个预热 {settings["warmup"]} × 1 秒，采样 {settings["iterations"]} × 1 秒；单线程，AverageTime，JMH 1.37，GC profiler。' + (' <b>SMOKE：仅验证流程，不用于正式排名。</b>' if environment["profile"] != "standard" else ''),
        "__TABLES__": render_tables(rows),
        "__PREFLIGHT__": '<table><tr><th>操作</th><th>输入</th><th>状态</th><th>诊断</th></tr>' + ''.join(pre) + '</table>',
        "__LIBRARIES__": '<table><tr><th>上游</th><th>提交</th><th>测量边界</th></tr>' + ''.join(libraries) + '</table>',
        "__EXCLUDED__": ''.join(excluded),
    }
    template = (root / "report-template.html").read_text(encoding="utf-8")
    for marker, replacement in replacements.items():
        template = template.replace(marker, replacement)
    (root / "report.html").write_text(template, encoding="utf-8")
    print(f"Generated report.html with {len(rows)} measurements")

if __name__ == "__main__":
    generate()
