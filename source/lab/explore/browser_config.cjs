// Host configuration only; agents never receive these paths or host APIs.
const fs=require('node:fs');
const {chromium}=require(process.env.BOUNDARY_PLAYWRIGHT_MODULE||'playwright');
const macChrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const executablePath=process.env.BOUNDARY_CHROME_BIN||(process.platform==='darwin'&&fs.existsSync(macChrome)?macChrome:undefined);
module.exports={chromium,executablePath};
