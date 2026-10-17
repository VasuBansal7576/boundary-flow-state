import unittest
from unittest.mock import patch

from lab.codex_worker import CodexWorker


class ContainmentTests(unittest.TestCase):
    def test_untrusted_urls_cannot_change_the_target_authority(self):
        for path in ['https://example.com', '//example.com', '/\\example.com', 'file:///etc/passwd']:
            with self.subTest(path=path), patch('lab.codex_worker.httpx.request') as request:
                worker = CodexWorker('researcher', 'baseline', 'test')
                with self.assertRaises(ValueError):
                    worker.http({'method': 'GET', 'path': path})
                request.assert_not_called()

    def test_budget_exhaustion_does_not_send_another_request(self):
        worker = CodexWorker('researcher', 'baseline', 'test', max_calls=0)
        with patch('lab.codex_worker.httpx.request') as request:
            result = worker.http({'method': 'GET', 'path': '/api/catalog'})
            self.assertIn('budget exhausted', result['error'])
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
