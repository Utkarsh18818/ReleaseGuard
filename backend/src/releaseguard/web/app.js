const $ = id => document.getElementById(id);
const state = { report: null, tasks: [], run: null, job: null, health: null, service: null, tab: 'map', offline: false, busy: false };
const signatures = {};
let refreshing = false;
let requestKey = null;
let dialogReturnFocus = null;
const labels = { 'release-brief': 'Release brief', catalog: 'Service catalog', 'incident-record': 'Incident record', 'history-record': 'Past incident record', 'check-record': 'Integration check' };
const stageLabels = { queued: 'Waiting for a worker', running: 'Starting review', investigating: 'Following connected evidence', awaiting_verifier: 'Findings saved for verification', verifying: 'Checking the findings', acting: 'Recording the decision', completed: 'Review complete', rejected: 'Findings not accepted', stale: 'Evidence changed', incomplete: 'Review incomplete', failed: 'Review interrupted' };
const active = job => job && ['queued', 'running'].includes(job.state);
const title = value => String(value || '').replaceAll(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const time = value => value ? new Date(value * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Not recorded';
const duration = ms => Number.isFinite(ms) ? `${(ms / 1000).toFixed(1)} s` : 'Not measured';
const sourceLabel = id => labels[id] || (id.startsWith('source-event-') ? 'Demo evidence update' : title(id));

function element(tag, className = '', content) {
  const node = document.createElement(tag);
  node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}
function icon(name, extra = '') {
  const node = element('i', `icon ${extra}`);
  node.style.setProperty('--icon', `url('/assets/icons/${name}.svg')`);
  node.setAttribute('aria-hidden', 'true');
  return node;
}
document.querySelectorAll('[data-icon]').forEach(node => node.style.setProperty('--icon', `url('/assets/icons/${node.dataset.icon}.svg')`));

async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(25000),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || data.error || `Request failed (${response.status})`);
  return data;
}
const releasePath = () => `/api/releases/${encodeURIComponent($('release').value)}`;
function changed(name, value) {
  const signature = JSON.stringify(value);
  if (signatures[name] === signature) return false;
  signatures[name] = signature;
  return true;
}
function notice(message, error = false) {
  $('notice').hidden = !message;
  $('notice').textContent = message;
  $('notice').className = `notice${error ? ' error' : ''}`;
}
function openDialog(name, eyebrow = 'RELEASEGUARD') {
  $('dialog').classList.remove('video-dialog');
  dialogReturnFocus = document.activeElement;
  $('dialogTitle').textContent = name;
  $('dialogEyebrow').textContent = eyebrow;
  $('dialogContent').replaceChildren();
  if (!$('dialog').open) $('dialog').showModal();
  $('closeDialog').focus();
  closeNavigation();
  return $('dialogContent');
}
function closeNavigation() { document.body.classList.remove('nav-open'); $('mobileMenu').setAttribute('aria-expanded', 'false'); }
$('closeDialog').onclick = () => $('dialog').close();
$('dialog').addEventListener('close', () => {
  const target = innerWidth <= 720 && dialogReturnFocus?.closest('.sidebar') ? $('mobileMenu') : dialogReturnFocus?.isConnected ? dialogReturnFocus : $('review');
  target?.focus({ preventScroll: true });
});
$('dialog').addEventListener('click', e => { if (e.target === $('dialog')) { const r = $('dialog').getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) $('dialog').close(); } });
$('mobileMenu').onclick = () => { const open = document.body.classList.toggle('nav-open'); $('mobileMenu').setAttribute('aria-expanded', String(open)); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNavigation(); });
document.addEventListener('click', e => { if (!e.target.closest('.sidebar') && !e.target.closest('#mobileMenu')) closeNavigation(); });
function scrollTo(id) { closeNavigation(); $(id).scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); }

function showGuide(scopeOnly = false) {
  const box = openDialog(scopeOnly ? 'What does “Ready” mean?' : 'Your release review, explained', 'A QUICK GUIDE');
  box.append(element('p', 'guide-intro', 'ReleaseGuard helps an engineering lead answer one question: can this release move forward based on the recorded evidence?'));
  const steps = [
    ['Follow the connected services', 'A Checkout release can depend on Payments, which can depend on Ledger. ReleaseGuard follows those links to find relevant incidents instead of treating each service separately.'],
    ['Check the evidence and remember past fixes', 'It checks recorded incidents, ownership and integration verification. The agent can look up previous attempts, including fixes that made an earlier incident worse.'],
    ['Give a traceable decision and a responsible owner', 'Current checks produce Ready, Blocked, Needs evidence or Review outdated. A verified blocker can create a task for its recorded owner. You can inspect the source behind each finding.'],
  ];
  steps.forEach(([heading, text], i) => { const row = element('div', 'guide-step'); const content = element('div'); content.append(element('h3', '', heading), element('p', '', text)); row.append(element('span', 'guide-number', String(i + 1)), content); box.append(row); });
  box.append(element('div', 'callout', 'Ready means the configured checks passed for the modeled scope and recorded evidence. It is not a guarantee that a deployment is safe. ReleaseGuard does not deploy software.'));
  box.append(element('p', 'muted small', 'This workspace uses a fictional company and synthetic test/incident records. Demo controls change this sample evidence, not a production system.'));
}
$('help').onclick = () => showGuide(); $('quickHelp').onclick = () => showGuide(); $('scopeHelp').onclick = () => showGuide(true);
$('navActivity').onclick = e => { e.preventDefault(); scrollTo('activity'); };
$('explainDecision').onclick = () => { selectTab(state.report?.blockers?.length ? 'findings' : 'map'); scrollTo('evidence'); };

function showSources(ids, heading = 'Evidence library') {
  const report = state.report;
  const box = openDialog(heading, 'SOURCE-BACKED EVIDENCE');
  if (!report || !ids.length) { box.append(element('p', '', 'No evidence has been retrieved for this review yet.')); return; }
  box.append(element('p', 'section-intro', `Evidence snapshot from review revision ${report.revision}. ${state.offline ? 'Connection lost; current freshness cannot be confirmed.' : report.effective_status === 'Needs reassessment' ? 'This review is outdated. Run a new review before relying on it.' : 'Sources below support the recorded review.'}`));
  [...new Set(ids)].forEach(id => {
    const source = report.sources[id];
    const document = element('article', 'source-document');
    document.append(element('h3', '', sourceLabel(id)));
    if (!source) { document.append(element('p', '', 'Source unavailable. This claim cannot be verified from the saved evidence.')); }
    else {
      document.append(element('p', 'source-meta', `${id} · version ${source.version ?? 'unrecorded'} · ${source.synthetic ? 'Synthetic source' : 'Recorded source'}`), element('p', 'source-text', source.text));
      const checksum = element('details'); const summary = element('summary', '', 'Source checksum'); checksum.append(summary, element('p', 'checksum', source.checksum || 'Not recorded')); document.append(checksum);
    }
    box.append(document);
  });
}
function sourceButtons(ids) {
  const links = element('div', 'source-links');
  [...new Set(ids)].forEach(id => { const button = element('button', 'source-link'); button.title = `Source: ${id}`; button.append(icon('file-text'), document.createTextNode(sourceLabel(id))); button.onclick = () => showSources([id], sourceLabel(id)); links.append(button); });
  return links;
}
$('navSources').onclick = () => showSources(Object.keys(state.report?.sources || {}));
$('metricSources').onclick = $('navSources').onclick;

function renderDecision() {
  const data = state.report;
  let kind = 'loading', label = 'Not reviewed', headline = 'Review this release to get started.', reason = 'ReleaseGuard will check the connected services, recorded incidents and required verification.', symbol = 'search';
  if (state.offline) { kind = 'offline'; label = 'Connection lost'; headline = 'Current status can’t be confirmed.'; reason = 'The evidence service is unavailable. Previous findings remain historical until the connection is restored.'; symbol = 'triangle-alert'; }
  else if (data) {
    const status = data.effective_status;
    if (status === 'Ready') { kind = 'ready'; label = 'Ready'; headline = 'Recorded checks passed.'; reason = `No blocking incidents were found across ${data.paths.length} connected services, and the required checks passed. Review the evidence before proceeding.`; symbol = 'circle-check'; }
    else if (status === 'Blocked') { kind = 'blocked'; label = 'Blocked'; headline = 'Resolve the blockers before release.'; reason = `${data.blockers.filter(b => b.supported).length} supported blocking incident${data.blockers.filter(b => b.supported).length === 1 ? '' : 's'} affect${data.blockers.filter(b => b.supported).length === 1 ? 's' : ''} a connected service. The owner and supporting evidence are below.`; symbol = 'shield-check'; }
    else if (status === 'Needs reassessment') { kind = 'stale'; label = 'Review outdated'; headline = 'The evidence changed. Review again.'; reason = `${data.freshness_reason || 'Connected evidence is no longer current'}. The previous decision should not be used as a current release recommendation.`; symbol = 'refresh-cw'; }
    else { kind = 'insufficient'; label = 'Needs evidence'; headline = 'There isn’t enough evidence yet.'; reason = data.missing_checks[0] || 'Required evidence is missing or contradictory. Resolve the checks below, then review again.'; symbol = 'triangle-alert'; }
  }
  $('decisionCard').className = `decision-card ${kind}`;
  $('statusPill').textContent = label; $('decisionTitle').textContent = headline; $('decisionReason').textContent = reason;
  $('decisionIcon').replaceChildren(icon(symbol));
  const meta = $('decisionMeta'); meta.replaceChildren();
  if (data) {
    const reviewed = element('span'); reviewed.append(icon('clock'), document.createTextNode(`Reviewed ${time(data.assessed_at)}`));
    const scope = element('span'); scope.append(icon('file-text'), document.createTextNode(`${Object.keys(data.sources).length} recorded sources`));
    const freshness = element('span'); freshness.append(icon(kind === 'stale' || state.offline ? 'refresh-cw' : 'check-check'), document.createTextNode(kind === 'stale' ? 'New review required' : state.offline ? 'Freshness unknown' : 'Freshness checked'));
    freshness.title = `Last server freshness check: ${time(data.checked_at)}`;
    meta.append(reviewed, scope, freshness);
  }
  $('servicesMetric').textContent = data ? data.paths.length : '—';
  $('blockersMetric').textContent = data ? data.blockers.filter(b => b.supported).length : '—';
  $('sourcesMetric').textContent = data ? Object.keys(data.sources).length : '—';
  $('sourceCount').textContent = data ? Object.keys(data.sources).length : '—';
  $('reviewTime').textContent = active(state.job) ? 'Review is running in the background' : data ? `Last review ${time(data.assessed_at)}` : 'No review yet';
}

function selectTab(name) {
  state.tab = name;
  document.querySelectorAll('[data-tab]').forEach(tab => { const selected = tab.dataset.tab === name; tab.classList.toggle('active', selected); tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1; $(`panel-${tab.dataset.tab}`).hidden = !selected; });
  if (name === 'map') requestAnimationFrame(drawEdges);
}
const tabs = [...document.querySelectorAll('[data-tab]')];
tabs.forEach((tab, index) => {
  tab.onclick = () => selectTab(tab.dataset.tab);
  tab.onkeydown = event => {
    let next = index;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = tabs.length - 1;
    else return;
    event.preventDefault(); selectTab(tabs[next].dataset.tab); tabs[next].focus();
  };
});

let visibleNodes = [];
function renderEvidence() {
  const data = state.report;
  if (!data) return;
  $('findingCount').textContent = data.blockers.length; $('historyCount').textContent = data.memory.length;
  const map = $('serviceMap'); map.replaceChildren();
  const blocked = new Set(data.blockers.map(b => b.service_id));
  const paths = [...data.paths].sort((a, b) => a.path.length - b.path.length || a.service_id.localeCompare(b.service_id));
  visibleNodes = paths.slice(0, 24);
  map.style.gridTemplateColumns = `repeat(${Math.max(1, ...visibleNodes.map(p => p.path.length))}, minmax(120px,1fr))`;
  const rows = {};
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.classList.add('map-edges'); svg.setAttribute('aria-hidden', 'true'); map.append(svg);
  visibleNodes.forEach(path => {
    const node = element('button', `map-node${path.path.length === 1 ? ' root' : ''}${blocked.has(path.service_id) ? ' blocked' : ''}`);
    node.dataset.service = path.service_id;
    const top = element('span', 'node-top'); top.append(icon(path.path.length === 1 ? 'git-branch' : 'database'), document.createTextNode(title(path.service_id)));
    node.append(top, element('span', 'node-kind', path.path.length === 1 ? 'Changed service' : 'Release dependency'));
    if (blocked.has(path.service_id)) node.append(element('span', 'node-badge', 'Blocking incident'));
    node.style.gridColumn = path.path.length; node.style.gridRow = rows[path.path.length] = (rows[path.path.length] || 0) + 1;
    node.onclick = () => inspectService(path.service_id);
    map.append(node);
  });
  if (!paths.some(p => p.service_id === state.service)) state.service = paths[0]?.service_id;
  inspectService(state.service);
  const list = $('pathList'); list.replaceChildren();
  paths.filter(p => p.path.length > 1).slice(0, 24).forEach(path => { const button = element('button', 'path-chip'); button.append(icon('git-branch'), document.createTextNode(path.path.map(title).join(' → ')), icon('file-text')); button.title = 'Open sources for this dependency path'; button.onclick = () => showSources(path.source_ids, 'Evidence for this dependency path'); list.append(button); });
  if (paths.length > 24) list.append(element('p', 'small muted', `Map shows 24 of ${paths.length} services in scope. Source records remain available in the evidence library.`));
  renderFindings(); renderHistory(); requestAnimationFrame(drawEdges);
}
function inspectService(id) {
  if (!state.report) return;
  const path = state.report.paths.find(p => p.service_id === id);
  if (!path) return;
  state.service = id;
  document.querySelectorAll('.map-node').forEach(node => { const selected = node.dataset.service === id; node.classList.toggle('selected', selected); node.setAttribute('aria-pressed', String(selected)); });
  const box = $('serviceInspector'); box.replaceChildren();
  const heading = element('div', 'inspector-heading'); heading.append(element('strong', '', title(id)), element('span', 'neutral-pill', path.path.length === 1 ? 'This release changes this service' : 'In the release dependency path'));
  const blockers = state.report.blockers.filter(b => b.service_id === id);
  box.append(heading, element('p', '', path.path.length === 1 ? 'This is where the release’s modeled changes begin. Follow its dependencies to understand related risks.' : `Connected through ${path.path.map(title).join(' → ')}. ${blockers.length ? `${blockers.length} blocking incident is recorded for this service.` : 'No blocking incident for this service appears in this review.'}`), sourceButtons(path.source_ids));
}
function drawEdges() {
  const map = $('serviceMap'), svg = map.querySelector('svg');
  if (!svg || state.tab !== 'map') return;
  const rect = map.getBoundingClientRect(); svg.replaceChildren(); svg.setAttribute('viewBox', `0 0 ${map.clientWidth} ${map.clientHeight}`);
  const ns = 'http://www.w3.org/2000/svg';
  const defs = document.createElementNS(ns, 'defs'); const marker = document.createElementNS(ns, 'marker'); marker.setAttribute('id', 'dependency-arrow'); marker.setAttribute('viewBox', '0 0 10 10'); marker.setAttribute('refX', '8'); marker.setAttribute('refY', '5'); marker.setAttribute('markerWidth', '5'); marker.setAttribute('markerHeight', '5'); marker.setAttribute('orient', 'auto-start-reverse'); const arrow = document.createElementNS(ns, 'path'); arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 Z'); arrow.setAttribute('fill', '#9fb8c2'); marker.append(arrow); defs.append(marker); svg.append(defs);
  const nodes = new Map([...map.querySelectorAll('.map-node')].map(node => [node.dataset.service, node]));
  const seen = new Set();
  visibleNodes.forEach(item => item.path.slice(1).forEach((id, i) => {
    const start = nodes.get(item.path[i]), end = nodes.get(id), key = `${item.path[i]}\0${id}`;
    if (!start || !end || seen.has(key)) return; seen.add(key);
    const a = start.getBoundingClientRect(), b = end.getBoundingClientRect();
    const x1 = a.right - rect.left + 1, y1 = a.top + a.height / 2 - rect.top, x2 = b.left - rect.left - 6, y2 = b.top + b.height / 2 - rect.top;
    const curve = document.createElementNS(ns, 'path'); const mid = (x1 + x2) / 2;
    curve.setAttribute('d', `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`); curve.setAttribute('fill', 'none'); curve.setAttribute('stroke', '#b6c8d1'); curve.setAttribute('stroke-width', '1.4'); curve.setAttribute('marker-end', 'url(#dependency-arrow)'); svg.append(curve);
  }));
}
new ResizeObserver(() => requestAnimationFrame(drawEdges)).observe($('serviceMap'));
document.fonts.ready.then(drawEdges);

function renderFindings() {
  const box = $('findings'), data = state.report; box.replaceChildren();
  if (!data.blockers.length) {
    const empty = element('div', 'empty-state'), copy = element('div'); copy.append(element('h3', '', 'No blocking incidents in this review'), element('p', '', 'The recorded release checks did not find an unresolved blocking incident in the connected services. This applies only to the modeled scope and evidence.')); empty.append(icon('circle-check'), copy); box.append(empty);
  }
  data.blockers.forEach(blocker => {
    const item = element('article', 'finding'); const label = element('span', 'inline-label caution'); label.append(icon('triangle-alert'), document.createTextNode(blocker.supported ? 'Supported blocking incident' : 'Incident evidence incomplete'));
    item.append(label, element('h3', '', blocker.summary), element('p', 'route', blocker.path.map(title).join(' → ')), element('p', '', `Responsible team: ${blocker.owner?.name || 'Not confirmed — action withheld'}`), sourceButtons(blocker.source_ids)); box.append(item);
  });
  if (data.missing_checks.length) { box.append(element('h3', '', 'Evidence still needed')); data.missing_checks.forEach(check => box.append(element('p', 'section-intro', check))); }
}
function renderHistory() {
  const box = $('history'); box.replaceChildren();
  if (!state.report.memory.length) box.append(element('p', 'empty', 'No relevant historical attempts were retrieved. The agent should not claim a lesson from past fixes.'));
  state.report.memory.forEach(attempt => {
    const item = element('article', 'history-item'); const adverse = attempt.observed_outcome.toLowerCase().includes('worsened');
    const label = element('span', `inline-label${adverse ? ' caution' : ''}`); label.append(icon(adverse ? 'triangle-alert' : 'history'), document.createTextNode(adverse ? 'Historical caution' : 'Historical observation'));
    item.append(label, element('h3', '', attempt.technique), element('p', '', attempt.observed_outcome), element('p', 'muted small', 'A recorded outcome from an earlier incident. Present applicability needs verification.'), sourceButtons([attempt.source_id])); box.append(item);
  });
}

function renderNextStep() {
  const box = $('nextStep'), data = state.report; box.replaceChildren();
  let heading = 'Start with a release review', copy = 'Choose a release and select Review release. The agent will investigate related evidence and explain its findings.', action = 'Review release', fn = startReview;
  if (state.offline) { heading = 'Restore the evidence connection'; copy = 'The current decision cannot be confirmed. The application will check for reconnection automatically.'; action = 'Check connection'; fn = () => refresh(true); }
  else if (data?.effective_status === 'Needs reassessment') { heading = 'Run a fresh review'; copy = data.freshness_reason || 'A relevant fact or verification changed. Recheck before using the old recommendation.'; }
  else if (data?.blockers.some(b => b.supported)) { const blocker = data.blockers.find(b => b.supported); heading = `Resolve ${title(blocker.service_id)}’s blocker`; copy = `${blocker.owner?.name || 'The service owner'} needs to investigate “${blocker.summary}”. Its source-backed path is available below.`; action = 'Inspect blocking evidence'; fn = () => { selectTab('findings'); scrollTo('evidence'); }; }
  else if (data?.missing_checks.length) { heading = 'Provide the missing evidence'; copy = data.missing_checks.join('. '); action = 'View required checks'; fn = () => { selectTab('findings'); scrollTo('evidence'); }; }
  else if (data) { heading = 'Review the evidence, then decide'; copy = 'The recorded checks passed. Confirm that this modeled scope and verification match the release you intend to make.'; action = 'Inspect release evidence'; fn = () => { selectTab('map'); scrollTo('evidence'); }; }
  box.append(element('h3', '', heading), element('p', '', copy));
  const button = element('button', 'button subtle'); button.append(document.createTextNode(action), icon('arrow-right')); button.onclick = fn; if (fn === startReview && active(state.job)) button.disabled = true; box.append(button);
  const run = state.run;
  if (run?.state === 'completed' && run.fresh && !state.offline && run.explanation?.review?.length) {
    const note = element('p', '', `Agent follow-up: review the recorded “${run.explanation.review[0].technique}”. Validate its suitability before any production change.`); box.append(element('p', 'subtle-label', 'HISTORICAL CONTEXT · NOT A GUARANTEED FIX'), note);
  }
}
function renderTasks() {
  const tasks = state.tasks.filter(task => task.release_id === $('release').value).sort((a, b) => Number(b.status === 'open') - Number(a.status === 'open'));
  $('actionCount').textContent = tasks.length; const box = $('tasks'); box.replaceChildren();
  if (!tasks.length) { box.append(element('p', 'empty', 'No tasks recorded for this release. A supported blocker with a confirmed owner can create one.')); return; }
  tasks.forEach(task => {
    let evidence = {}; try { evidence = JSON.parse(task.evidence); } catch { /* display only known fields */ }
    const item = element('article', 'task'), top = element('div', 'task-top');
    top.append(element('span', 'team-avatar', task.owner.slice(0, 1)), element('strong', 'task-owner', task.owner), element('span', `task-state${task.status === 'open' ? ' open' : ''}`, title(task.status)));
    item.append(top, element('p', '', evidence.summary || 'Recorded release blocker'));
    if (evidence.source_ids?.length) item.append(sourceButtons(evidence.source_ids)); box.append(item);
  });
}

function renderActivity() {
  const run = state.run, job = state.job, running = active(job);
  const outcome = running ? 'running' : job?.state || run?.state;
  const badge = { completed: 'Reviewed & saved', running: 'Review in progress', queued: 'Queued', incomplete: 'Incomplete', rejected: 'Not accepted', stale: 'Outdated', failed: 'Interrupted' };
  $('agentStatus').textContent = badge[outcome] || 'No agent review yet';
  $('activitySummary').textContent = running ? 'The review continues in the background. You can leave this page and come back.' : run?.state === 'completed' ? `The saved agent review used ${run.tool_calls} tool calls and a separate verification step.${run.fresh ? '' : ' Its evidence has since changed.'}` : run ? 'The review did not produce a verified current result. No completed agent outcome is being substituted.' : 'Select Review release to start a source-backed investigation. A quick guide explains each step.';
  const phases = [['queued', 'Queued'], ['investigating', 'Evidence'], ['verifying', 'Verification'], ['acting', 'Decision']];
  const events = job?.events || [], completed = outcome === 'completed';
  let phase = running ? 0 : completed ? 4 : -1;
  for (const event of events) { const i = phases.findIndex(([name]) => name === event.stage); if (i >= 0) phase = i; }
  if (completed) phase = 4;
  const timeline = $('timeline'); timeline.replaceChildren();
  phases.forEach(([name, label], index) => {
    const done = completed || index < phase, current = running && index === phase;
    const item = element('li', done ? 'done' : current ? 'current' : 'pending'); const dot = element('span', 'step-dot'); dot.append(icon(done ? 'check' : current ? 'loader-circle' : 'circle-dot', current ? 'spinning' : ''));
    const event = events.find(e => e.stage === name);
    item.append(dot, element('span', 'step-title', label), element('span', 'step-time', event ? time(event.at) : completed ? 'Complete' : current ? 'In progress' : '—')); timeline.append(item);
  });
  const note = $('agentNote'); note.replaceChildren(); note.className = 'agent-note';
  if (job?.dispatch_error) { note.classList.add('error'); note.append(element('p', '', 'Your request is saved, but the worker queue is unavailable. It will be retried within the recovery budget.')); }
  if (!running && run?.error) { note.classList.add('error'); note.append(element('p', '', run.error)); }
  if (!running && run?.verification_issues?.length) { note.classList.add('error'); run.verification_issues.forEach(issue => note.append(element('p', '', issue))); }
  if (!running && run?.state === 'completed' && run.explanation) {
    run.explanation.avoid.forEach(attempt => note.append(element('p', '', `Historical caution: “${attempt.technique}” previously ${attempt.observed_outcome.toLowerCase()}. ${run.fresh ? '' : 'This is from an older review.'}`)));
    note.append(element('p', '', 'A separate verifier checked the findings. Release rules, not model prose, determined the final verdict.'));
  } else if (run?.actions_withheld) note.append(element('p', '', 'Agent actions were withheld. Any earlier release decision is a separate recorded result.'));
  const retry = !running && run?.state === 'incomplete' && run.proposal && run.model_calls < 5 && run.request_key;
  $('retry').hidden = !retry || state.health?.public_demo;
  renderTechnical();
}
function renderTechnical() {
  const run = state.run, data = state.report, job = state.job, box = $('technicalContent'); box.replaceChildren();
  const grid = element('div', 'technical-grid');
  const records = [['Model / API time', duration(run?.timing?.model_ms)], ['Graph client time', duration(run?.timing?.graph_client_ms ?? data?.timing?.graph_client_ms)], ['Model calls / tools', run ? `${run.model_calls} / ${run.tool_calls}` : 'No model run'], ['Canonical verdict', data?.effective_status || 'Not assessed']];
  records.forEach(([name, value]) => { const item = element('div'); item.append(element('strong', '', name), element('p', '', value)); grid.append(item); }); box.append(grid);
  if (data) box.append(element('p', 'small', `Assessed revision ${data.revision}; current revision ${data.current_revision}. Freshness checked ${time(data.checked_at)}. Dataset: synthetic Northstar Shop.`));
  if (run) { box.append(element('p', 'trace-line', `Run: ${run.id}`), element('p', 'trace-line', `State: ${run.state}; source snapshot: revision ${run.revision}`)); run.trace.forEach(step => box.append(element('p', 'trace-line', `${step.tool}(${JSON.stringify(step.arguments)})`))); }
  if (job) box.append(element('p', 'trace-line', `Job: ${job.id}; delivery attempts ${job.attempts}/3`));
  box.append(element('p', 'small muted', 'Model time is cumulative across resumed invocations. Graph server time is a subset of client time. Final checkpoint and freshness reads are outside the stored timing scope.'));
}

function render() {
  $('publicDemo').hidden = !state.health?.public_demo;
  renderDecision();
  const data = state.report;
  if (changed('evidence', data && [data.id, data.current_revision, data.effective_status, data.paths, data.blockers, data.missing_checks, data.sources, data.memory])) renderEvidence();
  if (changed('tasks', state.tasks)) renderTasks();
  if (changed('agent', [state.run?.id, state.run?.state, state.run?.fresh, state.run?.model_calls, state.run?.tool_calls, state.run?.trace, state.run?.error, state.run?.verification_issues, state.job, state.report?.effective_status, state.report?.current_revision])) renderActivity();
  if (changed('next-step', [state.report?.id, state.report?.effective_status, state.report?.current_revision, state.report?.freshness_reason, state.run?.id, state.run?.state, state.run?.fresh, state.offline, active(state.job)])) renderNextStep();
  const connected = !state.offline && state.health?.graph === 'reachable';
  $('connection').className = `connection${connected ? '' : ' offline'}`;
  $('connection').lastElementChild.textContent = connected ? `FalkorDB ${state.health.database_target === 'cloud' ? 'Cloud' : 'Local'} · connected` : 'Evidence connection unavailable';
  $('review').disabled = state.busy || active(state.job) || state.health?.visual_preview;
  $('review').title = state.health?.visual_preview ? 'Read-only local design preview. The deployed app remains separate.' : '';
  $('review').querySelector('span').textContent = active(state.job) ? 'Review running' : state.busy ? 'Saving request…' : 'Review release';
}
async function refresh(includeHealth = false) {
  if (refreshing) return;
  refreshing = true;
  let fetched = false;
  try {
    const root = releasePath();
    const [report, tasks, run, job, health] = await Promise.all([api(`${root}/latest`), api('/api/tasks'), api(`${root}/agent-investigations/latest`), api(`${root}/jobs/latest`), includeHealth || !state.health || state.offline ? api('/api/health') : Promise.resolve(state.health)]);
    const finished = active(state.job) && job?.id === state.job.id && !active(job);
    Object.assign(state, { report, tasks, run, job, health, offline: false });
    if (finished) notice('');
    fetched = true;
    if (state.connectionError) notice('Connection restored. Current evidence is available again.');
    state.connectionError = false;
    render();
  } catch (error) {
    if (fetched) { console.error(error); notice('The evidence loaded, but part of the display failed. Refresh this page to try again.', true); }
    else { state.offline = true; state.connectionError = true; render(); notice(`Connection interrupted. ${error.message}. Current release status is not confirmed.`, true); }
  } finally { refreshing = false; }
}
async function mutate(path, payload, message) {
  if (state.busy) return;
  state.busy = true; render();
  try { const result = await api(path, payload); notice(message); await refresh(); return result; }
  catch (error) { notice(error.message, true); throw error; }
  finally { state.busy = false; render(); }
}
async function startReview() {
  if (state.busy || active(state.job)) return;
  requestKey ||= crypto.randomUUID();
  try {
    const job = await mutate(`${releasePath()}/agent-investigations`, { request_key: requestKey }, 'Review requested. The agent is following connected evidence; progress is saved below.');
    if (job) { state.job = job; requestKey = null; render(); scrollTo('activity'); }
  } catch { /* retain key after an uncertain HTTP outcome; replay is idempotent */ }
}
$('review').onclick = startReview;
$('retry').onclick = async () => {
  try { const job = await mutate(`${releasePath()}/agent-verifier-resume`, { request_key: state.run.request_key }, 'Saved verification queued again within the existing model budget.'); if (job) { state.job = job; render(); } } catch { /* error already visible */ }
};
$('release').onchange = () => { state.service = null; state.report = null; state.run = null; state.job = null; requestKey = null; refresh(true); };

function openDemo() {
  const box = openDialog('See how the decision changes', 'DEMO LAB · SYNTHETIC DATA ONLY');
  box.append(element('p', 'guide-intro', 'Change a sample fact, then review the release again. This changes the fictional Northstar workspace. It never deploys software.'));
  box.append(element('div', 'callout', 'Try: add a Ledger incident → observe the old review become outdated → review again → inspect the Checkout → Payments → Ledger path and the owner-assigned blocker.'));
  const options = [
    ['Add a blocking Ledger incident', 'Adds a synthetic incident to a dependency two hops from Checkout.', 'Add incident', '/api/demo/events', { kind: 'new_incident', entity_id: 'inc-13', value: 'ledger' }],
    ['Resolve the added Ledger incident', 'After adding INC-13, mark it resolved and review again. Required checks must still pass.', 'Resolve INC-13', '/api/demo/events', { kind: 'incident_status', entity_id: 'inc-13', value: 'resolved' }],
    ['Resolve the Payments incident', 'Marks INC-12 resolved. Other incidents and missing checks can still block the release.', 'Resolve INC-12', '/api/demo/events', { kind: 'incident_status', entity_id: 'inc-12', value: 'resolved' }],
    ['Make verification expire', 'Demonstrates why a release cannot rely on outdated test evidence.', 'Expire check', '/api/demo/events', { kind: 'verification_result', entity_id: 'integration-check', value: 'expire' }],
    ['Record a passing check', 'Adds a synthetic passing verification record. This does not run real CI.', 'Record pass', '/api/demo/events', { kind: 'verification_result', entity_id: 'integration-check', value: 'pass' }],
    ['Run the rules without the model', 'Checks the same graph evidence with deterministic policy. This is separate from a completed agent review.', 'Check rules', `${releasePath()}/assessments`, {}],
    ['Load the sample company', 'Imports the synthetic fixture idempotently. It does not reset every changed incident.', 'Load fixture', '/api/demo/seed', null],
  ];
  options.forEach(([heading, copy, label, path, payload]) => {
    const row = element('div', 'demo-option'), content = element('div'), button = element('button', 'button subtle', label);
    content.append(element('h3', '', heading), element('p', '', copy));
    button.disabled = state.busy || active(state.job) || state.health?.demo_enabled === false;
    button.onclick = async () => {
      button.disabled = true;
      try { await mutate(path, payload === null ? {} : { ...payload, request_key: crypto.randomUUID() }, 'Sample evidence updated. Check the current decision and review again when needed.'); $('dialog').close(); }
      catch { button.disabled = false; }
    };
    row.append(content, button); box.append(row);
  });
}
$('navDemo').onclick = openDemo;

async function initialize() {
  try {
    const releases = await api('/api/releases');
    if (releases.length) { const current = $('release').value; $('release').replaceChildren(...releases.map(release => { const option = element('option', '', release.name); option.value = release.id; return option; })); if (releases.some(r => r.id === current)) $('release').value = current; }
    await refresh(true);
  } catch (error) { state.offline = true; render(); notice(`Could not load release evidence. ${error.message}`, true); }
}
let workspaceStarted = false;
function startWorkspace() {
  if (workspaceStarted) return;
  workspaceStarted = true;
  initialize();
}
document.addEventListener('releaseguard:workspace', startWorkspace);
if (!document.body.classList.contains('intro-active')) startWorkspace();
setInterval(() => { if (workspaceStarted && !document.body.classList.contains('intro-active') && !state.busy && !document.hidden) refresh(); }, 4000);
setInterval(() => { if (state.report?.expires_at && Date.now() >= state.report.expires_at * 1000 && state.report.effective_status !== 'Needs reassessment') { state.report = { ...state.report, effective_status: 'Needs reassessment', freshness_reason: 'Verification evidence expired' }; render(); } }, 1000);
