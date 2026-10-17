const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const fs=require('node:fs/promises');
(async()=>{const b=await chromium.launch({headless:true});try{
const context=await b.newContext();const p=await context.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});await p.goto(process.env.RELEASEGUARD_UI_URL || 'http://127.0.0.1:8000');await p.waitForFunction(()=>['Ready','Blocked','Review outdated','Needs evidence'].includes(document.querySelector('#statusPill')?.textContent));
const runs=[];for(const state of ['desktop','guide','source','mobile']){if(state==='guide') await p.getByRole('button',{name:'Quick guide',exact:true}).click();if(state==='source'){await p.keyboard.press('Escape');await p.locator('[data-service="payments"]').click();await p.locator('#serviceInspector').getByRole('button',{name:'Service catalog',exact:true}).click();}if(state==='mobile'){await p.keyboard.press('Escape');await p.setViewportSize({width:390,height:844});}
const result=await new AxeBuilder({page:p}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();runs.push({state,violations:result.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))});}
await fs.writeFile('outputs/ui-review/accessibility.json',JSON.stringify(runs,null,2));console.log(JSON.stringify(runs,null,2));if(runs.some(run=>run.violations.length))process.exitCode=1;
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});

