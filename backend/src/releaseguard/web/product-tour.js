// Progressive, motion-aware playback. No graph writes or third-party player requests.
const preview = document.getElementById('productTour');
const toggle = document.getElementById('toggleTour');
const watch = document.getElementById('watchDemo');
const dialog = document.getElementById('dialog');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let userPaused = reduced.matches;
let inView = false;
let fullVideo = null;
let fullReturnFocus = null;

document.querySelectorAll('[data-open-workspace]').forEach(button => button.addEventListener('click', () => {
  document.body.classList.remove('intro-active');
  document.querySelector('.skip-link').href = '#main';
  preview.pause();
  window.scrollTo(0, 0);
  document.getElementById('main').focus({preventScroll:true});
  document.dispatchEvent(new Event('releaseguard:workspace'));
}));
document.getElementById('showIntro').addEventListener('click', () => {
  document.body.classList.add('intro-active');
  document.querySelector('.skip-link').href = '#introContent';
  window.scrollTo(0, 0);
  document.querySelector('.intro-brand').focus({preventScroll:true});
  reconcilePlayback();
});

function syncButton() {
  const paused = preview.paused;
  toggle.setAttribute('aria-label', `${paused ? 'Play' : 'Pause'} product preview`);
  toggle.querySelector('span').textContent = paused ? 'Play' : 'Pause';
  toggle.querySelector('i').style.setProperty('--icon', `url('/assets/icons/${paused ? 'play' : 'pause'}.svg')`);
}
async function playPreview() {
  if (!preview.querySelector('source').src) {
    preview.querySelector('source').src = preview.querySelector('source').dataset.src;
    preview.load();
  }
  try { await preview.play(); } catch { /* Poster and manual play remain available. */ }
  syncButton();
}
function reconcilePlayback() {
  if (inView && !document.hidden && !dialog.open && !userPaused) playPreview();
  else preview.pause();
}
preview.addEventListener('play', syncButton);
preview.addEventListener('pause', syncButton);
preview.addEventListener('error', () => {
  toggle.disabled = true;
  toggle.querySelector('span').textContent = 'Preview unavailable';
});
toggle.addEventListener('click', () => {
  userPaused = !preview.paused;
  if (userPaused) preview.pause(); else playPreview();
});
new IntersectionObserver(entries => {
  inView = entries[0].isIntersecting;
  reconcilePlayback();
}, { threshold: 0.2 }).observe(preview);
document.addEventListener('visibilitychange', reconcilePlayback);
reduced.addEventListener('change', () => { userPaused = reduced.matches; reconcilePlayback(); });

function showDemo() {
  fullReturnFocus = document.activeElement;
  preview.pause();
  dialog.classList.add('video-dialog');
  document.getElementById('dialogEyebrow').textContent = 'RECORDED DEMONSTRATION';
  document.getElementById('dialogTitle').textContent = 'ReleaseGuard in action';
  const content = document.getElementById('dialogContent');
  content.replaceChildren();
  fullVideo = document.createElement('video');
  fullVideo.className = 'full-demo-video';
  fullVideo.controls = true;
  fullVideo.playsInline = true;
  fullVideo.preload = 'metadata';
  fullVideo.poster = '/demo-media/demo-poster.jpg';
  fullVideo.src = '/demo-media/ReleaseGuard-demo.mp4';
  fullVideo.setAttribute('aria-label', 'ReleaseGuard narrated demonstration');
  const captions = document.createElement('track');
  Object.assign(captions, { kind: 'captions', label: 'English', srclang: 'en', src: '/demo-media/captions.vtt' });
  fullVideo.append(captions);
  const note = document.createElement('p');
  note.className = 'demo-video-note';
  note.textContent = 'Synthetic company data · real recorded execution · AI narration. Edited from separate takes with shortened waiting time. This video shows an earlier recorded state, not the current decision.';
  const fallback = document.createElement('a');
  fallback.href = 'https://youtu.be/qnejDVhVe-E';
  fallback.target = '_blank';
  fallback.rel = 'noopener noreferrer';
  fallback.textContent = 'Watch on YouTube';
  fallback.className = 'demo-video-fallback';
  content.append(fullVideo, note, fallback);
  dialog.showModal();
  document.getElementById('closeDialog').focus();
  fullVideo.play().catch(() => {});
}
watch.addEventListener('click', showDemo);
document.querySelectorAll('[data-watch-demo]').forEach(button => button.addEventListener('click', showDemo));
dialog.addEventListener('close', () => {
  if (!fullVideo) return;
  fullVideo.pause();
  fullVideo.removeAttribute('src');
  fullVideo.load();
  fullVideo = null;
  dialog.classList.remove('video-dialog');
  (fullReturnFocus?.isConnected ? fullReturnFocus : watch).focus({ preventScroll: true });
  reconcilePlayback();
});
syncButton();
