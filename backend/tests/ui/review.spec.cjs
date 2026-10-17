/* UI contracts. Recorded responses below test presentation, not backend/model correctness. */
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const base = process.env.RELEASEGUARD_UI_URL || 'http://127.0.0.1:8000';
const output = path.resolve('outputs/ui-review');
const results = [];
const stateAccessibility = [];
let browser;

(async () => {
  await fs.mkdir(output, {recursive:true});
  browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce',timezoneId:'Asia/Kolkata'});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', message => {if(message.type()==='error') errors.push(message.text());});
  const record = async (name, test) => {await test();results.push({name,status:'passed'});console.log('PASS '+name);};
  const waitForLoaded = async target => {
    await target.waitForFunction(()=>['Ready','Blocked','Review outdated','Needs evidence'].includes(document.querySelector('#statusPill')?.textContent));
    await target.waitForFunction(()=>document.querySelector('#agentStatus')?.textContent !== 'Loading activity');
    await target.evaluate(()=>document.fonts.ready);
  };
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await waitForLoaded(page);
  const liveLabel = await page.locator('#statusPill').textContent();
  const realReport = await (await page.request.get(base+'/api/releases/checkout-v2.4/latest')).json();
  const realRun = await (await page.request.get(base+'/api/releases/checkout-v2.4/agent-investigations/latest')).json();
  const realTasks = await (await page.request.get(base+'/api/tasks')).json();
  const realJob = await (await page.request.get(base+'/api/releases/checkout-v2.4/jobs/latest')).json();
  await record('Live release decision appears before technical activity',async()=>{
    const decision=await page.locator('#decisionCard').boundingBox(); const activity=await page.locator('#activity').boundingBox();
    assert(decision.y<activity.y && decision.y+decision.height<1000);
    assert.equal(await page.locator('#servicesMetric').textContent(),String(realReport.paths.length));
    assert.equal(await page.locator('#sourcesMetric').textContent(),String(Object.keys(realReport.sources).length));
    assert.equal(await page.locator('#technical').getAttribute('open'),null);
    assert.equal(await page.locator('#notice').isVisible(),false);
    if(realTasks.some(task=>task.status==='open')) assert.equal(await page.locator('#tasks .task-state').first().textContent(),'Open');
    assert.equal(await page.locator('#tasks').innerText().then(text=>text.includes('Source Event ')),false);
  });
  await record('Real dependency selection and source preview survive polling',async()=>{
    await page.locator('[data-service="payments"]').click();
    assert.match(await page.locator('#serviceInspector').innerText(),/Payments/);
    const source=page.locator('#serviceInspector').getByRole('button',{name:'Service catalog',exact:true});
    await source.click(); await page.waitForTimeout(4500);
    assert.equal(await page.locator('#dialog').isVisible(),true);
    assert.match(await page.locator('#dialogContent').innerText(),/Checkout depends on Payments/);
    await page.screenshot({path:path.join(output,'04-redesign-source.png')});
    await page.keyboard.press('Escape');
    assert.equal(await source.evaluate(el=>el===document.activeElement),true);
  });
  await record('Evidence tabs support keyboard navigation',async()=>{
    await page.getByRole('tab',{name:'Service map',exact:true}).focus(); await page.keyboard.press('End');
    assert.equal(await page.getByRole('tab',{name:/Past fixes/}).getAttribute('aria-selected'),'true');
    assert.match(await page.locator('#panel-history').innerText(),/Overload worsened/);
    await page.keyboard.press('Home');
    assert.equal(await page.getByRole('tab',{name:'Service map',exact:true}).getAttribute('aria-selected'),'true');
  });
  await record('Technical details and focus stay open across refresh',async()=>{
    await page.locator('#technical>summary').click(); await page.waitForTimeout(4500);
    assert.notEqual(await page.locator('#technical').getAttribute('open'),null);
    assert.equal(await page.locator('#technical>summary').evaluate(el=>el===document.activeElement),true);
    await page.locator('#technical>summary').click();
  });
  await record('Quick guide explains the product and its limits',async()=>{
    await page.getByRole('button',{name:'Quick guide',exact:true}).click();
    assert.match(await page.locator('#dialogContent').innerText(),/can this release move forward/);
    assert.match(await page.locator('#dialogContent').innerText(),/does not deploy software/);
    await page.keyboard.press('Escape');
  });
  await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:path.join(output,'03-redesign-desktop-viewport.png')});
  await page.screenshot({path:path.join(output,'03-redesign-desktop.png'),fullPage:true});
  await record('Mobile layout contains its graph and navigation',async()=>{
    await page.setViewportSize({width:390,height:844}); await page.waitForTimeout(250); await page.evaluate(()=>scrollTo(0,0));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.getByRole('button',{name:'Open navigation',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Open navigation',exact:true}).getAttribute('aria-expanded'),'true');
    await page.getByRole('button',{name:'Demo lab',exact:true}).click();
    assert.match(await page.locator('#dialogContent').innerText(),/fictional Northstar workspace/);
    assert.equal(await page.getByRole('button',{name:'Add incident',exact:true}).count(),1);
    await page.keyboard.press('Escape');
    await page.waitForFunction(()=>document.activeElement?.id==='mobileMenu');
    assert.equal(await page.locator('#mobileMenu').evaluate(el=>el===document.activeElement),true);
    assert.equal(await page.evaluate(()=>document.body.classList.contains('nav-open')),false);
    await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:path.join(output,'05-redesign-mobile-viewport.png')});
    await page.screenshot({path:path.join(output,'05-redesign-mobile.png'),fullPage:true});
  });
  const blockedFixture=JSON.parse(await fs.readFile('outputs/configuration/background-live-result.json','utf8'));
  const recordedBlocked=blockedFixture.run.assessment;
  const clone = value => structuredClone(value);
  const scenarios = [
    ['Blocked',{...clone(recordedBlocked),effective_status:'Blocked'},'Resolve the blockers before release.'],
    ['Review outdated',{...clone(realReport),effective_status:'Needs reassessment',freshness_reason:'Connected evidence changed',current_revision:realReport.revision+1},'The evidence changed. Review again.'],
    ['Needs evidence',{...clone(realReport),effective_status:'Insufficient evidence',missing_checks:['Fresh integration verification required for this release']},'There isn’t enough evidence yet.'],
  ];
  for(const [label,report,headline] of scenarios) {
    await record('Recorded UI-state fixture: '+label,async()=>{
      const fixtureContext=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
      const fixturePage=await fixtureContext.newPage();
      await fixturePage.route('**/api/**',async route=>{
        const pathname=new URL(route.request().url()).pathname;
        let response;
        if(pathname==='/api/releases') response=[{id:'checkout-v2.4',name:'Checkout v2.4'}];
        else if(pathname.endsWith('/health')) response={graph:'reachable',database_target:'cloud',demo_enabled:true};
        else if(pathname==='/api/tasks') response=label==='Blocked'?[]:realTasks;
        else if(pathname.endsWith('/jobs/latest')) response=null;
        else if(pathname.endsWith('/agent-investigations/latest')) response=label==='Blocked'?blockedFixture.run:{...clone(realRun),fresh:false};
        else response=report;
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(response)});
      });
      await fixturePage.goto(base); await fixturePage.waitForFunction(expected=>document.querySelector('#statusPill')?.textContent===expected,label);
      assert.equal(await fixturePage.locator('#decisionTitle').textContent(),headline);
      if(label==='Blocked') {
        await fixturePage.getByRole('tab',{name:/Blockers/}).click();
        assert.match(await fixturePage.locator('#findings').innerText(),/Money/);
        assert.match(await fixturePage.locator('#findings').innerText(),/Payments/);
      }
      await fixturePage.screenshot({path:path.join(output,`fixture-${label.toLowerCase().replaceAll(' ','-')}.png`),fullPage:true});
      const scan=await new AxeBuilder({page:fixturePage}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      stateAccessibility.push({state:label,violations:scan.violations});
      await fs.writeFile(path.join(output,'state-accessibility.json'),JSON.stringify(stateAccessibility,null,2));
      assert.deepEqual(scan.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),[]);
      await fixtureContext.close();
    });
  }
  await record('UI queue state keeps the saved decision separate from an unfinished review',async()=>{
    const p=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const job={id:'ui-only-recorded-job',release_id:'checkout-v2.4',state:'queued',attempts:0,events:[{stage:'queued',at:Date.now()/1000}]};
    let submitted=false;
    await p.route('**/api/**',async route=>{
      const u=new URL(route.request().url()).pathname;
      let response=realReport;
      if(u==='/api/releases')response=[{id:'checkout-v2.4',name:'Checkout v2.4'}];
      else if(u.endsWith('/health'))response={graph:'reachable',database_target:'cloud',demo_enabled:true};
      else if(u==='/api/tasks')response=realTasks;
      else if(u.endsWith('/jobs/latest'))response=submitted?job:null;
      else if(u.endsWith('/agent-investigations/latest'))response=realRun;
      else if(route.request().method()==='POST'){submitted=true;response=job;}
      await route.fulfill({status:route.request().method()==='POST'?202:200,contentType:'application/json',body:JSON.stringify(response)});
    });
    await p.goto(base);await waitForLoaded(p);await p.locator('#review').click();
    await p.waitForFunction(()=>document.querySelector('#agentStatus')?.textContent==='Review in progress');
    assert.equal(await p.getByRole('button',{name:'Review running',exact:true}).isDisabled(),true);
    assert.match(await p.locator('#activitySummary').innerText(),/background/);
    assert.equal(await p.locator('#statusPill').textContent(),liveLabel);
    await p.close();
  });
  await record('Dependency failure withholds a current release presentation',async()=>{
    await page.route('**/api/**',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":"graph_unavailable"}'}));
    await page.waitForFunction(()=>document.querySelector('#statusPill')?.textContent==='Connection lost',null,{timeout:12000});
    assert.match(await page.locator('#decisionReason').innerText(),/unavailable/);
    await page.unroute('**/api/**');
    await page.waitForFunction(()=>['Ready','Blocked','Review outdated','Needs evidence'].includes(document.querySelector('#statusPill')?.textContent),null,{timeout:12000});
  });
  assert.deepEqual(errors.filter(error=>!error.includes('503 (Service Unavailable)')),[]);
  await fs.writeFile(path.join(output,'ui-test-results.json'),JSON.stringify({base,results,liveReads:true,recordedStateTests:true,note:'Route fixtures test presentation only. They do not establish backend/model outcomes.'},null,2));
  await browser.close();
})().catch(async error=>{console.error(error);await fs.writeFile(path.join(output,'ui-test-results.json'),JSON.stringify({results,error:error.message},null,2));process.exitCode=1;}).finally(async()=>{await browser?.close();});
