import os
import unittest
from unittest.mock import patch
from lab.mcp_server import validate_request, bound_context

class MCPContainmentTests(unittest.TestCase):
    def test_arbitrary_remote_destinations_and_header_injection_refused(self):
        for path in ['https://example.com/x', '//example.com/x', '\\evil', '/api/x\\evil']:
            with self.subTest(path=path), self.assertRaises(ValueError):validate_request('GET',path,'')
    def test_non_http_methods_and_oversized_actions_refused(self):
        for method,payload in [('CONNECT',''),('TRACE',''),('POST','x'*30001)]:
            with self.subTest(method=method), self.assertRaises(ValueError):validate_request(method,'/api/resources',payload)
    def test_read_and_adversarial_write_use_same_transport_contract(self):
        validate_request('GET','/api/resources/water-public','')
        validate_request('PATCH','/api/resources/water-public','{"content":"synthetic test"}')
    def test_identity_bound_by_launcher_and_all_256_ids_supported(self):
        for peer in ['agent-001','agent-256']:
            with patch.dict(os.environ,{'BOUNDARY_MCP_ARM':'protected','BOUNDARY_MCP_AGENT':peer,'BOUNDARY_MCP_PORT':'8187'}):
                self.assertEqual(bound_context(),('protected',peer,8187))
    def test_unregistered_profile_and_nonlocal_port_refused(self):
        for key,value in [('BOUNDARY_MCP_AGENT','agent-257'),('BOUNDARY_MCP_ARM','other'),('BOUNDARY_MCP_PORT','443')]:
            env={'BOUNDARY_MCP_ARM':'protected','BOUNDARY_MCP_AGENT':'agent-001','BOUNDARY_MCP_PORT':'8187',key:value}
            with patch.dict(os.environ,env),self.assertRaises(ValueError):bound_context()
