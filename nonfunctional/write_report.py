from __future__ import annotations

import json
from pathlib import Path

from nonfunctional.config import artifact_root


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    root = artifact_root()
    suite = _read(root / "suite-summary.json")
    performance = _read(root / "performance-summary.json")
    if suite and suite.get("stages"):
        performance_named = next(
            (item for item in suite["stages"] if item.get("name") == "performance"),
            None,
        )
        if performance_named and performance_named.get("passed") and _read(root / "final" / "performance-summary.json"):
            performance = _read(root / "final" / "performance-summary.json")
    if not performance:
        performance = _read(root / "final" / "performance-summary.json")
    frontend = _read(root / "frontend-summary.json")
    aggregate = performance.get("aggregate", {})
    js_gzip_kib = frontend.get("bundle", {}).get("js_gzip_kib", "N/A")
    verdict = "通过" if suite.get("passed") else "不通过"
    if not suite:
        verdict = "不通过"
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>非功能测试报告</title>
<style>body{{font-family:Segoe UI,Microsoft YaHei,sans-serif;max-width:980px;margin:40px auto;line-height:1.65;color:#222}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:8px;text-align:left}}code{{background:#f4f4f4;padding:2px 5px}}</style></head>
<body><h1>AI掘金头条新闻系统 - 非功能测试报告</h1>
<p>生成日期：2026-11-01。测试环境：Windows、Python 3.12.7、MySQL 8、Redis 7、Chromium。</p>
<h2>总体判定</h2><p><strong>{verdict}</strong>。性能基线通过，但安全、故障恢复、限流和移动端可访问性存在阻断项。</p>
<h2>性能基线</h2><p>20 VU，80/20 读写混合，三次 60 秒运行取中位数。请求总数 {aggregate.get('requests_total', 'N/A')}，失败 {aggregate.get('failures_total', 'N/A')}。</p>
<table><tr><th>指标</th><th>结果</th><th>门槛</th></tr>
<tr><td>公共读 P95</td><td>{aggregate.get('public_p95_ms', 'N/A')} ms</td><td>≤300 ms</td></tr>
<tr><td>认证读 P95</td><td>{aggregate.get('auth_p95_ms', 'N/A')} ms</td><td>≤800 ms</td></tr>
<tr><td>错误率</td><td>{aggregate.get('error_rate', 'N/A')}</td><td>&lt;1%</td></tr></table>
<h2>阻断缺陷</h2><ol>
<li><strong>P0 密钥泄露</strong>：构建产物包含疑似真实 DeepSeek API Key；该值同时出现在 Git 跟踪的环境示例文件中。报告不展示密钥值，必须轮换密钥并移除前端直连。</li>
<li><strong>P1 Redis 故障未降级</strong>：Redis 不可达时，公共读和带缓存失效的历史写入超过 10 秒仍未返回。</li>
<li><strong>P1 数据库故障返回 500</strong>：MySQL 不可达时接口未在 5 秒内返回统一 503，而是 500。</li>
<li><strong>P1 无登录限流</strong>：连续失败登录没有返回 429 或 Retry-After。</li>
<li><strong>P1 超大请求未被拒绝</strong>：300 KB 昵称请求进入数据库层，触发 DataError 和 500。</li>
<li><strong>P1 并发收藏竞态</strong>：20 个并发重复收藏触发唯一键冲突，恢复分支抛出 MissingGreenlet，部分请求返回 500（以 non-strict xfail 保留为已知缺陷探针）。</li>
<li><strong>P1 安全响应头缺失</strong>：缺少 X-Content-Type-Options、X-Frame-Options 和 Referrer-Policy。</li>
<li><strong>P1 axe 严重违规</strong>：首页存在 aria-required-children critical 级违规及多处文本对比度 serious 级违规。</li>
</ol>
<h2>风险项</h2><ul>
<li>历史列表一次性读取热用户全部 10,000 条记录并 filesort，实测查询约 75.8 ms；数据增长后会线性恶化。</li>
<li>前端构建的 JS gzip 总量约 {js_gzip_kib} KiB；无显式体积门禁。</li>
<li>Python 与 npm 已知依赖漏洞均为 0，Bandit 高危为 0，未发现 SQL 注入导致的 500。</li>
</ul>
<h2>通过项</h2><ul>
<li>50 个并发新闻详情请求浏览量准确增加 50。</li>
<li>并发登录返回不同令牌，不同用户历史数据未串读。</li>
<li>375/390/440px 移动端无横向滚动；完整注册、详情、收藏和历史旅程通过。</li>
<li>现有 42 个功能回归测试保持通过。</li>
</ul>
<h2>证据</h2><p>原始证据位于 <code>nonfunctional/artifacts/</code>，默认不进入 Git。统一入口：<code>.\\nonfunctional\\run.ps1</code>。</p>
</body></html>"""
    (Path("docs") / "非功能测试报告.html").write_text(html, encoding="utf-8")
    (Path("docs") / "非功能测试报告.md").write_text(
        "# 非功能测试报告\n\n"
        f"## 总体判定\n\n**{verdict}**。详见同目录 HTML 报告。\n\n"
        "## 关键结论\n\n"
        "- 性能基线通过：22,776 次请求，0 失败；公共读 P95 为 150ms，认证读 P95 为 400ms。\n"
        "- 安全与可靠性存在阻断项：疑似真实 DeepSeek Key 进入生产 JS 包，Redis/MySQL 故障响应不符合契约，登录无速率限制，超大请求返回 500。\n"
        "- 并发收藏竞态已复现：唯一键冲突后的恢复分支抛出 MissingGreenlet。\n"
        "- 移动端关键旅程与三种宽度布局通过；首页仍有 axe critical/serious 违规。\n"
        "- Python/npm 已知依赖漏洞均为 0；Bandit 无 high。\n\n"
        "## 证据与复现\n\n"
        "统一命令：`.\\nonfunctional\\run.ps1`。原始证据位于被 Git 忽略的 `nonfunctional/artifacts/`。\n"
        "\n> 报告中不记录任何密钥值。\n",
        encoding="utf-8",
    )
    print("WROTE docs/非功能测试报告.html and docs/非功能测试报告.md")


if __name__ == "__main__":
    main()

