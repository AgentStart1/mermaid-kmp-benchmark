import unittest
import json
import tempfile
from pathlib import Path
import generate_report

class ReportTests(unittest.TestCase):
    def test_escapes_external_diagnostic(self):
        self.assertEqual(generate_report.esc('<script>"&'), '&lt;script&gt;&quot;&amp;')

    def test_empty_measurements_are_not_zero_scores(self):
        self.assertEqual(generate_report.render_tables([]), '')

    def test_separates_stages_and_escapes_names(self):
        def row(operation):
            return {"params": {"operation": operation, "caseName": "simple_flowchart"}, "primaryMetric": {"score": 2.5, "scoreError": 0.1, "scoreConfidence": [2.4, 2.6]}}
        report = generate_report.render_tables([row('a<script>:parse'), row('b:svg')])
        self.assertIn('a&lt;script&gt;', report)
        self.assertNotIn('a<script>', report)
        self.assertEqual(report.count('<table>'), 2)
        self.assertIn('2.500', report)
        self.assertIn('chart-card', report)
        self.assertIn('单库测量', report)

    def test_rust_kmp_appears_only_in_svg_comparison(self):
        rows = [
            {"params": {"operation": "rust-kmp:svg", "caseName": "simple_flowchart"}, "primaryMetric": {"score": 10.0}},
            {"params": {"operation": "native:svg", "caseName": "simple_flowchart"}, "primaryMetric": {"score": 20.0}},
            {"params": {"operation": "native:parse", "caseName": "simple_flowchart"}, "primaryMetric": {"score": 2.0}},
        ]
        report = generate_report.render_tables(rows)
        svg, parse = report.split('<section id="parse">')
        self.assertIn('mermaid-rust-kmp', svg)
        self.assertNotIn('mermaid-rust-kmp', parse)
        self.assertIn('耗时 2.00×', svg)
        self.assertIn('rust-kmp-simple_flowchart.svg', svg)

    def test_failed_preflight_is_visible_and_never_becomes_a_score(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "results").mkdir()
            (root / "report-template.html").write_text("__TABLES__ __PREFLIGHT__")
            fixtures = {
                "results/jmh.json": [],
                "results/environment.json": {"settings": {"forks": 2, "warmup": 5, "iterations": 8}, "profile": "standard", "os": "test", "architecture": "test", "cpu": "test", "java": "test", "started_utc": "test", "failures": []},
                "results/preflight.json": [{"operation": "test:parse", "caseName": "complex_flowchart", "status": "failed", "error": "<bad>"}],
                "discovery.json": {"candidates": []},
            }
            for name, value in fixtures.items():
                (root / name).write_text(json.dumps(value))
            generate_report.generate(root)
            report = (root / "report.html").read_text()
            self.assertIn("failed", report)
            self.assertIn("&lt;bad&gt;", report)
            self.assertNotIn("0.000", report)

if __name__ == '__main__':
    unittest.main()
