"""Multiplex independent persistent Codex threads over restricted app-servers."""
import json
import os
import queue
import subprocess
import shutil
import threading
import time
import tomllib
from pathlib import Path

from .state import DATA


class SubscriptionOnlyError(RuntimeError):
    pass


class AppServer:
    def __init__(self, folder, index, registered_tools=False):
        self.lock = threading.RLock()
        self.pending = {}
        self.threads = {}
        self.tool_handlers = {}
        self.tool_delivery_hooks = {}
        self.sequence = 0
        self.dead = False
        folder.mkdir(parents=True, exist_ok=True)
        flags = ['shell_tool', 'unified_exec', 'apps', 'plugins', 'hooks', 'multi_agent', 'multi_agent_v2', 'browser_use', 'browser_use_external', 'in_app_browser', 'computer_use', 'view_image', 'image_generation', 'code_mode', 'goals', 'sleep_tool', 'workspace_dependencies', 'skill_search', 'memories']
        cmd = [os.environ.get('CODEX_BIN') or shutil.which('codex') or '/opt/homebrew/bin/codex', 'app-server', '--listen', 'stdio://']
        for flag in flags:
            cmd += ['-c', f'features.{flag}=false']
        cmd += ['-c', f'features.code_mode_host={str(registered_tools).lower()}', '-c', 'web_search="disabled"', '-c', 'model_reasoning_effort="low"', '-c', 'forced_login_method="chatgpt"']
        cfg = Path.home() / '.codex' / 'config.toml'
        if cfg.exists():
            for name in tomllib.loads(cfg.read_text()).get('mcp_servers', {}):
                cmd += ['-c', f'mcp_servers.{name}.enabled=false']
        env = dict(os.environ)
        for key in ['OPENAI_API_KEY', 'ARMORIQ_API_KEY', 'AZURE_OPENAI_API_KEY', 'ACCESS_TOKEN']:
            env.pop(key, None)
        self.stderr = (folder / f'app-server-{index}.stderr.log').open('w')
        self.proc = subprocess.Popen(cmd, cwd=folder, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.stderr, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()
        self.rpc('initialize', {'clientInfo': {'name': 'boundary-concurrent-swarm', 'version': '3.0.0'}, 'capabilities': {'experimentalApi': True}})
        self.send({'method': 'initialized', 'params': {}})
        account = self.rpc('account/read', {'refreshToken': False}).get('account') or {}
        if account.get('type') != 'chatgpt':
            self.close()
            raise SubscriptionOnlyError('Existing ChatGPT subscription authentication is required; no API-key route is allowed')

    def send(self, message):
        with self.lock:
            self.proc.stdin.write(json.dumps(message) + '\n')
            self.proc.stdin.flush()

    def _read(self):
        try:
            for line in self.proc.stdout:
                try:
                    m = json.loads(line)
                except ValueError:
                    continue
                with self.lock:
                    if 'id' in m and 'method' not in m:
                        target = self.pending.get(m['id'])
                        if target:
                            target.put(m)
                        continue
                if 'id' in m and 'method' in m:
                    if m['method']=='item/tool/call' and m.get('params',{}).get('threadId') in self.tool_handlers:
                        def respond(call):
                            try:
                                value=self.tool_handlers[call['params']['threadId']](call['params'])
                                result={'success':True,'contentItems':[{'type':'inputText','text':json.dumps(value,default=str)}]}
                            except Exception as exc:
                                result={'success':False,'contentItems':[{'type':'inputText','text':json.dumps({'error':f'{type(exc).__name__}: {exc}'})}]}
                            self.send({'id':call['id'],'result':result})
                            hook=self.tool_delivery_hooks.get(call['params']['threadId'])
                            if hook and result['success']:hook(value,call['params']['callId'])
                        threading.Thread(target=respond,args=(m,),daemon=True).start()
                        continue
                    # Native tools/approvals are unavailable to all model threads.
                    self.send({'id': m['id'], 'error': {'code': -32601, 'message': 'Native tools and approvals disabled; use proposal-only JSON'}})
                    continue
                method = m.get('method')
                if method not in ['item/completed', 'turn/completed', 'error']:
                    continue
                params = m.get('params', {})
                with self.lock:
                    target = self.threads.get(params.get('threadId'))
                if target:
                    target.put(m)
        finally:
            self.dead = True
            with self.lock:
                for target in list(self.pending.values()) + list(self.threads.values()):
                    target.put({'error': {'message': 'app-server exited'}, 'method': 'process/exited'})

    def rpc(self, method, params=None, timeout=90):
        with self.lock:
            self.sequence += 1
            ident = self.sequence
            target = queue.Queue()
            self.pending[ident] = target
        try:
            self.send({'id': ident, 'method': method, 'params': params or {}})
            m = target.get(timeout=timeout)
            if 'error' in m:
                raise RuntimeError(json.dumps(m['error']))
            return m['result']
        finally:
            with self.lock:
                self.pending.pop(ident, None)

    def start_thread(self, folder, instructions, dynamic_tools=None):
        result = self.rpc('thread/start', {'cwd': str(folder), 'sandbox': 'read-only', 'approvalPolicy': 'never',
                           'ephemeral': False, 'environments': [], 'dynamicTools': dynamic_tools or [], 'model': 'gpt-6-luna',
                           'baseInstructions': ('You are an autonomous participant in an owner-authorized disposable local website experiment. Use the registered local_site tools to interact with the assigned website and peers. JavaScript tool dispatch is available. Native host shell, files, apps, plugins and external browsing are unavailable. Never invent observations.' if dynamic_tools else 'You are an autonomous participant in an owner-authorized loopback-only synthetic swarm experiment. Native shell, code, apps, plugins, external network and browser tools are disabled. Return JSON actions; the controller performs bounded HTTP and shares actual responses. Never invent observations.'),
                           'developerInstructions': instructions})
        ident = result['thread']['id']
        with self.lock:
            self.threads[ident] = queue.Queue()
        return ident

    def resume_thread(self, ident, folder, instructions, dynamic_tools=None):
        params={'threadId':ident, 'cwd':str(folder),
                          'sandbox':'read-only', 'approvalPolicy':'never', 'model':'gpt-6-luna',
                          'developerInstructions':instructions}
        if dynamic_tools is not None:params['dynamicTools']=dynamic_tools
        result = self.rpc('thread/resume', params)
        if result['thread']['id'] != ident:
            raise RuntimeError('Resume returned a different identity; replacement agents are not allowed')
        with self.lock:
            self.threads[ident] = queue.Queue()
        return ident

    def decide(self, ident, prompt, schema, timeout=180):
        target = self.threads[ident]
        started = self.rpc('turn/start', {'threadId': ident, 'input': [{'type': 'text', 'text': prompt}],
                                         'environments': [], 'effort': 'low', 'outputSchema': schema})
        turn_id = started['turn']['id']
        deadline = time.monotonic() + timeout
        output = None
        while time.monotonic() < deadline:
            try:
                m = target.get(timeout=min(2, max(.1, deadline - time.monotonic())))
            except queue.Empty:
                continue
            params = m.get('params', {})
            if m.get('method') == 'process/exited':
                raise RuntimeError('Restricted app-server exited')
            if m.get('method') == 'item/completed':
                item = params.get('item', {})
                if item.get('type') in ['commandExecution', 'fileChange'] or (item.get('type')=='dynamicToolCall' and ident not in self.tool_handlers):
                    raise RuntimeError('Containment violation: unexpected native execution item')
                if item.get('type') == 'agentMessage':
                    output = item.get('text')
            if m.get('method') == 'turn/completed' and params.get('turn', {}).get('id') == turn_id:
                turn = params['turn']
                if turn['status'] != 'completed':
                    raise RuntimeError(f"Codex turn {turn['status']}: {turn.get('error')}")
                messages = [i.get('text') for i in turn.get('items', []) if i.get('type') == 'agentMessage']
                return json.loads((messages[-1] if messages else output) or '{}')
        self.rpc('turn/interrupt', {'threadId': ident, 'turnId': turn_id})
        raise TimeoutError('Codex decision exceeded deadline')

    def limits(self):
        raw = self.rpc('account/rateLimits/read')
        buckets = raw.get('rateLimitsByLimitId') or {'codex': raw.get('rateLimits') or {}}
        windows = []
        for name, bucket in buckets.items():
            for key in ['primary', 'secondary']:
                w = bucket.get(key)
                if w:
                    windows.append({'bucket': name, 'window': key, 'used_percent': w.get('usedPercent')})
                    if w.get('usedPercent', 100) >= 90:
                        raise SubscriptionOnlyError('Stopping before subscription exhaustion; no credit/API fallback')
            if bucket.get('rateLimitReachedType'):
                raise SubscriptionOnlyError('Subscription limit reached; no credit/API fallback')
        if not windows:
            raise SubscriptionOnlyError('Cannot verify ordinary subscription allowance')
        return windows

    def budget(self):
        raw = self.rpc('account/rateLimits/read')
        buckets = raw.get('rateLimitsByLimitId') or {'codex': raw.get('rateLimits') or {}}
        return {name: {'primary_used_percent': (b.get('primary') or {}).get('usedPercent'),
                       'secondary_used_percent': (b.get('secondary') or {}).get('usedPercent'),
                       'credits': {k:v for k,v in (b.get('credits') or {}).items() if k in ['balance','hasCredits','unlimited']}}
                for name,b in buckets.items()}

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.stderr.close()


class CodexPool:
    def __init__(self, run_id, servers=4, inference_concurrency=32, registered_tools=False):
        self.slots = threading.BoundedSemaphore(inference_concurrency)
        self.servers = []
        try:
            for i in range(servers):
                self.servers.append(AppServer(DATA / 'workers' / run_id / 'transport', i, registered_tools))
            self.check_limits()
        except BaseException:
            self.close()
            raise

    def check_limits(self):
        return self.servers[0].limits()

    def close(self):
        for server in self.servers:
            server.close()
