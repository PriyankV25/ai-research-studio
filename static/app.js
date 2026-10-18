const $ = (selector) => document.querySelector(selector);
const form = $('#researchForm');
const topicInput = $('#topicInput');
const runButton = $('#runButton');
const errorBanner = $('#errorBanner');
const charCount = $('#charCount');
const stageOrder = ['search', 'reader', 'writer', 'critic'];
let currentJobId = null;
let pollTimer = null;
let startedAt = 0;
let timerInterval = null;
let latestReport = '';
let latestTopic = '';

function toast(message, isError = false) {
  const node = $('#toast'); node.textContent = message; node.classList.toggle('error', isError); node.classList.add('show');
  window.clearTimeout(toast._timer); toast._timer = window.setTimeout(() => node.classList.remove('show'), 2800);
}
function setError(message) { errorBanner.textContent = message; errorBanner.hidden = !message; }
function safeMarkdown(text) {
  const raw = window.marked ? marked.parse(text || '') : `<pre>${String(text || '').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</pre>`;
  return window.DOMPurify ? DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } }) : raw;
}
function setSystemStatus(data) {
  const status = $('#systemStatus'), hint = $('#systemHint'), line = document.querySelector('.system-line span');
  if (data.ok) { status.textContent = 'All systems configured'; hint.textContent = 'Groq + Tavily environment keys detected'; line.style.width = '100%'; }
  else { status.textContent = 'Setup required'; hint.textContent = `Missing ${data.missing_keys.join(' and ')} in your .env file`; line.style.width = '22%'; line.style.background = 'var(--amber)'; }
}
async function checkHealth() {
  try { const res = await fetch('/api/health'); const data = await res.json(); setSystemStatus(data); }
  catch { $('#systemStatus').textContent = 'Backend not reachable'; $('#systemHint').textContent = 'Start the Flask server to begin'; document.querySelector('.system-line span').style.width = '15%'; }
}
function setStage(stage, message) {
  const activeIndex = stageOrder.indexOf(stage);
  stageOrder.forEach((name, index) => {
    const card = document.querySelector(`.agent-card[data-stage="${name}"]`);
    const state = $(`#state-${name}`);
    card.classList.toggle('active', name === stage);
    card.classList.toggle('done', stage === 'completed' || (activeIndex >= 0 && index < activeIndex));
    state.textContent = stage === 'completed' || (activeIndex >= 0 && index < activeIndex) ? 'COMPLETE' : name === stage ? 'WORKING' : 'STANDBY';
    const step = document.querySelector(`.run-step[data-run-step="${name}"]`);
    if (step) {
      step.classList.toggle('active', name === stage);
      step.classList.toggle('done', stage === 'completed' || (activeIndex >= 0 && index < activeIndex));
      const label = step.querySelector('.run-step-status');
      label.textContent = stage === 'completed' || (activeIndex >= 0 && index < activeIndex) ? 'DONE' : name === stage ? 'RUNNING' : 'QUEUED';
    }
  });
  const widths = { search: 8, reader: 32, writer: 58, critic: 82, completed: 100, error: 100 };
  $('#railProgress').style.width = `${widths[stage] || 0}%`;
  $('#workflowMessage').textContent = message || 'Agents are working…';
  $('#elapsedTime').textContent = stage === 'completed' ? 'COMPLETE' : stage === 'error' ? 'ERROR' : `${Math.max(1, Math.floor((Date.now() - startedAt) / 1000))} SEC`;
}
function showRunning(topic) {
  $('#emptyState').hidden = true; $('#reportLayout').hidden = true; $('#resultActions').hidden = true; $('#runPanel').hidden = false;
  $('#runTopic').textContent = topic; startedAt = Date.now(); setStage('search', 'Starting your research run…');
  window.clearInterval(timerInterval); timerInterval = window.setInterval(() => {
    if (!$('#runPanel').hidden) $('#elapsedTime').textContent = `${Math.max(1, Math.floor((Date.now() - startedAt) / 1000))} SEC`;
  }, 1000);
}
function showResults(job) {
  window.clearInterval(timerInterval); $('#runPanel').hidden = true; $('#emptyState').hidden = true; $('#reportLayout').hidden = false; $('#resultActions').hidden = false;
  $('#reportDate').textContent = new Date().toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  $('#reportTitle').textContent = `Research: ${job.topic}`; $('#reportTopic').textContent = `Research question · ${job.topic}`;
  $('#reportBody').innerHTML = safeMarkdown(job.report || 'No report content was returned.');
  $('#criticBody').innerHTML = safeMarkdown(job.feedback || 'No critic feedback was returned.');
  latestReport = job.report || ''; latestTopic = job.topic || '';
  setStage('completed', 'Research report and critic review are ready.');
  $('#resultActions').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  toast('Research complete — your report is ready.');
}
function showFailure(job) {
  window.clearInterval(timerInterval); $('#runPanel').hidden = true; $('#emptyState').hidden = false;
  $('#emptyState h3').textContent = 'This research run hit a snag.';
  $('#emptyState p').textContent = job.error || 'An unexpected error occurred. Check your API keys and terminal logs, then try again.';
  setStage('error', 'The run stopped before completion.');
  setError(job.error || 'Research failed. Check your API keys and terminal output.');
  toast('Research run failed. Check the error message.', true);
}
async function pollJob(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}`); const job = await res.json();
    if (!res.ok) throw new Error(job.error || 'Could not retrieve job status.');
    setStage(job.stage, job.message);
    if (job.status === 'completed') { window.clearInterval(pollTimer); pollTimer = null; runButton.disabled = false; runButton.querySelector('.button-label').textContent = 'Run research'; showResults(job); }
    else if (job.status === 'failed') { window.clearInterval(pollTimer); pollTimer = null; runButton.disabled = false; runButton.querySelector('.button-label').textContent = 'Try again'; showFailure(job); }
  } catch (err) {
    window.clearInterval(pollTimer); pollTimer = null; runButton.disabled = false; runButton.querySelector('.button-label').textContent = 'Try again';
    setError(`Could not check the research status: ${err.message}`); toast('Lost connection to the local server.', true);
  }
}
form.addEventListener('submit', async (event) => {
  event.preventDefault(); const topic = topicInput.value.trim(); setError('');
  if (topic.length < 3) { setError('Please enter a research topic with at least 3 characters.'); topicInput.focus(); return; }
  if (pollTimer) window.clearInterval(pollTimer);
  runButton.disabled = true; runButton.querySelector('.button-label').textContent = 'Starting…'; showRunning(topic); $('#results').scrollIntoView({ behavior: 'smooth', block: 'start' });
  try {
    const res = await fetch('/api/research', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic }) });
    const data = await res.json(); if (!res.ok) throw new Error(data.error || 'Could not start research.');
    currentJobId = data.job_id; runButton.querySelector('.button-label').textContent = 'Research running';
    pollTimer = window.setInterval(() => pollJob(currentJobId), 1300); pollJob(currentJobId);
  } catch (err) {
    window.clearInterval(timerInterval); runButton.disabled = false; runButton.querySelector('.button-label').textContent = 'Try again';
    $('#runPanel').hidden = true; $('#emptyState').hidden = false; setError(`${err.message}. Make sure the Flask app is running and your .env is configured.`); toast('Could not start the research run.', true);
  }
});
topicInput.addEventListener('input', () => { charCount.textContent = `${topicInput.value.length} / 500`; if (!errorBanner.hidden) setError(''); });
document.querySelectorAll('.suggestion').forEach(btn => btn.addEventListener('click', () => { topicInput.value = btn.dataset.topic; topicInput.dispatchEvent(new Event('input')); topicInput.focus(); topicInput.scrollIntoView({ behavior: 'smooth', block: 'center' }); }));
document.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', () => { document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active')); btn.classList.add('active'); document.getElementById(btn.dataset.scroll)?.scrollIntoView({ behavior: 'smooth' }); }));
$('#backToTop').addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
$('#helpBtn').addEventListener('click', () => $('#aboutDialog').showModal());
$('#closeDialog').addEventListener('click', () => $('#aboutDialog').close());
$('#dialogDone').addEventListener('click', () => $('#aboutDialog').close());
$('#copyBtn').addEventListener('click', async () => { try { await navigator.clipboard.writeText(latestReport); toast('Report copied to clipboard.'); } catch { toast('Clipboard access was blocked by your browser.', true); } });
$('#downloadBtn').addEventListener('click', () => { const blob = new Blob([`# Research: ${latestTopic}\n\n${latestReport}\n`], { type: 'text/markdown;charset=utf-8' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `atlas-research-${latestTopic.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50) || 'report'}.md`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); toast('Markdown report exported.'); });
checkHealth();
