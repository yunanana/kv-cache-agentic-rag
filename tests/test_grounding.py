import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agents.grounding import unsupported_numbers, cited_page_texts
from agents.reviewer import to_source_tags, route_after_review, make_reviewer_node
from agents.exporter import make_exporter_node


class GroundingTests(unittest.TestCase):
    def test_unsupported_numbers(self):
        for claim in (
            '처리량 99.9% [P-HW p.10]',
            '처리량 99.9% [P-HW p. 10]',
            '리콜 0.123 [P-SW p.17]',
            '품질 손실 1~5% [P-HW p.10]',
            '처리량 99.9% [P-HW p.10][WM1]',
            '4배 압축 [P-SW pp. 17–19]',
        ):
            with self.subTest(claim=claim):
                self.assertTrue(unsupported_numbers(claim, lambda *_: 'no evidence'))

    def test_exact_number_and_page(self):
        claim = '처리량 35.7% [P-HW p.10]'
        self.assertFalse(unsupported_numbers(claim, lambda *_: 'throughput 35.7%'))
        self.assertTrue(unsupported_numbers(claim, lambda *_: '135.7%'))
        self.assertTrue(unsupported_numbers(claim, lambda s, p: '35.7%' if p == 11 else ''))

    def test_citation_numbers_are_not_claims(self):
        self.assertFalse(unsupported_numbers('설명 [P-SW p.17, p.19]', lambda *_: ''))

    def test_all_pages_and_missing_evidence(self):
        text = '[P-SW pp.1-10]'
        self.assertIn('p.10', cited_page_texts(text, lambda *_: 'evidence'))
        self.assertIn('검증 불가', cited_page_texts('[P-HW p.1]', lambda *_: ''))
        with self.assertRaises(ValueError):
            cited_page_texts(text, lambda *_: 'evidence', max_pages=8)

    def test_numbered_mixed_citations_preserved(self):
        report = '35.7% [1, pp. 10; 2]\n## REFERENCE\n1. arxiv 2606.12556\n2. web'
        tagged = to_source_tags(report)
        self.assertIn('[P-HW pp. 10][2]', tagged)
        self.assertTrue(unsupported_numbers(tagged, lambda *_: ''))

    def test_final_judge_receives_sources(self):
        judge = Mock()
        judge.invoke.return_value = SimpleNamespace(issues=[])
        prompt = Mock()
        prompt.__or__ = Mock(return_value=judge)
        with patch('agents.reviewer.REVIEW_PROMPT', prompt), \
             patch('agents.reviewer.get_verifier'), \
             patch('agents.reviewer.rule_check', return_value=([], 1)):
            node = make_reviewer_node(SimpleNamespace(page_text=lambda *_: 'ORIGINAL PAGE'))
            result = node({'report_md': '설명 [1, p.10]\n## REFERENCE\n1. 2606.12556',
                           'sources': [{'kind': 'web', 'id': 'WM1', 'url': 'example', 'content': 'WEB BODY'}]})
        evidence = judge.invoke.call_args.args[0]['evidence']
        self.assertIn('ORIGINAL PAGE', evidence)
        self.assertIn('WEB BODY', evidence)
        self.assertTrue(result['review']['passed'])

    def test_failed_review_is_not_approved(self):
        self.assertEqual(route_after_review({'review': {'passed': False}, 'revision_count': 999}), 'unverified')

    def test_failure_notice_reaches_pdf(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch('agents.exporter.OUTPUT_DIR', Path(tmp)), \
             patch('agents.exporter.save_pdf', return_value=1) as save:
            make_exporter_node('test.pdf')({'report_md': '# Report', 'sources': [],
                'review': {'passed': False, 'issues': ['test'], 'minor': []}})
            self.assertIn('검토 상태: 미통과', save.call_args.args[0])
            self.assertIn('검토 상태: 미통과', (Path(tmp) / 'report.md').read_text())


if __name__ == '__main__':
    unittest.main()
