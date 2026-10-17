// Real isolated Chromium pages. Agent traffic is restricted to the two lab origins.
const {chromium}=require('/Users/vasu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const http=require('node:http');
 let browser,contexts=new Map(),active=0,waiting=[];
async function enter(){if(active>=8)await new Promise(r=>waiting.push(r));active++}
function leave(){active--;waiting.shift()?.()}
async function session(key,origin,headers){
 let s=contexts.get(key);
 if(!s){
  const context=await browser.newContext({viewport:{width:1280,height:800},extraHTTPHeaders:headers,acceptDownloads:true});
  await context.route('**/*',route=>{
   const u=new URL(route.request().url());
   return u.origin===origin?route.continue():route.abort('blockedbyclient');
  });
  const page=await context.newPage();s={context,page,used:Date.now(),busy:false};contexts.set(key,s);
 }
 s.used=Date.now();s.busy=true;await s.context.setExtraHTTPHeaders(headers);return s;
}
async function execute(input){
 await enter();let s,events=[],pending=[];
 try{
  const origin=input.arm==='baseline'?'http://127.0.0.1:8173':'http://127.0.0.1:8174';
  s=await session((input.experiment||'preflight')+':'+input.arm+':'+input.agent,origin,input.headers);
  const listener=r=>{if(!r.url().startsWith(origin))return;pending.push((async()=>{let body;try{body=(await r.text()).slice(0,10000)}catch{body=''};events.push({url:r.url().replace(origin,''),method:r.request().method(),status:r.status(),body,decision_path:r.headers()['x-armoriq-decision-path'],check_id:r.headers()['x-boundary-check-id']})})())};
  s.page.on('response',listener);
  try{
   if(input.tool==='browse')await s.page.goto(origin+input.path,{waitUntil:'domcontentloaded',timeout:180000});
   else{
    if(s.page.url()==='about:blank')await s.page.goto(origin+(input.path||'/'),{waitUntil:'domcontentloaded',timeout:180000});
    await s.page.evaluate(()=>[...document.forms].forEach((f,i)=>f.id=f.id||'form-'+i));
    if(input.tool==='submit'){
     const f=s.page.locator(input.selector);await f.waitFor({timeout:10000});
     for(const [name,value]of Object.entries(input.fields||{}))await f.locator(`[name="${name.replaceAll('"','\\"')}"]`).fill(typeof value==='string'?value:JSON.stringify(value));
     const response=s.page.waitForResponse(r=>r.request().method()!=='GET',{timeout:180000}).catch(()=>null);
     await f.locator('button[type=submit]').click();await response;await s.page.locator('#result').filter({hasText:'status'}).waitFor({timeout:5000}).catch(()=>{});
    }else if(input.tool==='click')await s.page.locator(input.selector).click({timeout:15000});
   }
   await s.page.waitForLoadState('domcontentloaded');
   const dom=await s.page.evaluate(()=>({title:document.title,text:document.body.innerText.slice(0,14000),links:[...document.querySelectorAll('a[href]')].slice(0,80).map(a=>({text:a.innerText,href:a.getAttribute('href')})),forms:[...document.forms].map((f,i)=>{f.id=f.id||'form-'+i;return{selector:'#'+f.id,action:f.getAttribute('action'),method:f.dataset.method||f.method,fields:[...f.elements].filter(e=>e.name).map(e=>({name:e.name,value:e.value.slice(0,1000)}))}})}));
   // Flush asynchronous body capture before returning the actual network evidence.
   await Promise.all(pending);
   return {url:s.page.url().replace(origin,''),dom,network:events};
  }finally{s.page.off('response',listener)}
 }finally{
  if(s)s.busy=false;
  // Evict old inactive contexts only. A later action explicitly reopens its path.
  if(contexts.size>24){for(const [k,v]of [...contexts].sort((a,b)=>a[1].used-b[1].used)){if(contexts.size<=24)break;if(!v.busy){contexts.delete(k);await v.context.close()}}}
  leave();
 }
}
(async()=>{
 browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--disable-component-update','--disable-sync']});
 http.createServer(async(req,res)=>{
  if(req.url==='/health'){res.end(JSON.stringify({ok:true,contexts:contexts.size,active}));return}
  if(req.method!=='POST'||req.url!=='/action'){res.writeHead(404);res.end();return}
  let raw='';for await(const c of req){raw+=c;if(raw.length>100000){res.writeHead(413);res.end();return}}
  try{const input=JSON.parse(raw);if(!['baseline','protected'].includes(input.arm)||!/^agent-\d{3}$/.test(input.agent)||!['browse','submit','click'].includes(input.tool))throw Error('Invalid lab action');const p=input.path||'/';if(!p.startsWith('/')||p.startsWith('//')||p.includes('\\'))throw Error('Invalid local path');const result=await execute(input);res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result))}
  catch(e){res.writeHead(400,{'Content-Type':'application/json'});res.end(JSON.stringify({error:String(e)}))}
 }).listen(8176,'127.0.0.1',()=>process.stdout.write('Browser executor http://127.0.0.1:8176\n'));
})();
