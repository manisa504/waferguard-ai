'use strict';
const repo = 'https://github.com/manisa504/waferguard-ai/blob/main/';
const $ = id => document.getElementById(id);
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function field(parent, title, body) {
  parent.append(element('h4', title), element('p', body));
}
function postText(post) {
  return `${post.title}\n\n${post.business}\n\n${post.technical}\n\nEngineering decision: ${post.decision}\n\nArchitectural decision: ${post.architecture}\n\n${post.question}\n\nEvidence:\n${post.evidence.map(path => repo + path).join('\n')}`;
}
async function copy(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const label = button.textContent;
    button.textContent = 'Copied';
    $('feedback').textContent = 'Copied. Review the evidence and publication details before handing this to Hark.';
    setTimeout(() => { button.textContent = label; }, 2000);
  } catch {
    $('feedback').textContent = 'Clipboard access is unavailable. Download the Markdown brief, or select and copy the visible text.';
    button.insertAdjacentElement('afterend', element('span', ' Copy unavailable; select the text or download the brief.', 'muted'));
  }
}
function safeUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' ? url : null; } catch { return null; }
}
function media(config) {
  const video = config.videoUrl && safeUrl(config.videoUrl);
  if (video) {
    const host = video.hostname.replace(/^www\./, '');
    let embed;
    if (host === 'youtu.be') embed = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(video.pathname.slice(1))}`;
    if (host === 'youtube.com' && video.searchParams.get('v')) embed = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(video.searchParams.get('v'))}`;
    if (host === 'vimeo.com' && /^\/\d+$/.test(video.pathname)) embed = `https://player.vimeo.com/video/${video.pathname.slice(1)}`;
    const area = $('video-player');
    area.className = '';
    area.replaceChildren();
    if (embed) {
      const frame = element('iframe');
      frame.src = embed; frame.title = 'WaferGuard project walkthrough'; frame.className = 'video-frame';
      frame.loading = 'lazy'; frame.allowFullscreen = true;
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      area.append(frame);
    } else if (/\.(mp4|webm)$/i.test(video.pathname)) {
      const player = element('video'); player.src = video.href; player.controls = true;
      player.preload = 'metadata'; player.className = 'video-frame';
      player.setAttribute('aria-label', 'WaferGuard project walkthrough');
      area.append(player);
    }
    const link = element('a', 'Watch the supplied recording ↗'); link.href = video.href; area.append(link);
  }
  const app = config.vercelUrl && safeUrl(config.vercelUrl);
  if (app) { $('vercel-link').href = app.href; $('vercel-link').hidden = false; $('vercel-pending').hidden = true; }
}
async function main() {
  const response = await fetch('campaign.json');
  if (!response.ok) throw new Error('Campaign data could not be loaded.');
  const data = await response.json();
  const themes = [...new Set(data.days.map(post => post.theme))];
  for (const theme of themes) { const option = element('option', theme); option.value = theme; $('topic').append(option); }
  for (const post of data.days) { const link = element('a', `Day ${post.day} · ${post.theme}`); link.href = `#day-${post.day}`; link.dataset.day = post.day; $('day-nav').append(link); }
  function render() {
    const query = $('search').value.toLowerCase().trim();
    const selected = data.days.filter(post => (!$('topic').value || post.theme === $('topic').value) && postText(post).toLowerCase().includes(query));
    $('posts').replaceChildren();
    $('count').textContent = `${selected.length} of ${data.days.length} posts`;
    for (const link of $('day-nav').querySelectorAll('a')) link.hidden = !selected.some(post => String(post.day) === link.dataset.day);
    if (!selected.length) $('posts').append(element('p', 'No posts match. Clear the search or choose another topic.', 'no-results'));
    for (const post of selected) {
      const card = element('article', undefined, 'post'); card.id = `day-${post.day}`;
      const head = element('div', undefined, 'post-head');
      const title = element('div'); title.append(element('span', `Day ${post.day} / ${post.theme}`, 'tag'), element('h3', post.title));
      const button = element('button', 'Copy post', 'secondary'); button.type = 'button';
      button.setAttribute('aria-label', `Copy day ${post.day} post`);
      button.addEventListener('click', () => copy(postText(post), button)); head.append(title, button); card.append(head);
      field(card, 'Business context', post.business); field(card, 'Technical evidence', post.technical);
      field(card, 'Engineering decision', post.decision); field(card, 'Architectural decision', post.architecture);
      card.append(element('p', post.question, 'discussion'));
      const notes = element('details'); notes.append(element('summary', 'Visual direction'), element('p', post.visual)); card.append(notes);
      const evidence = element('div', undefined, 'evidence');
      for (const path of post.evidence) { const link = element('a', path.split('/').pop()); link.href = repo + path; evidence.append(link); }
      card.append(evidence); $('posts').append(card);
    }
  }
  $('search').addEventListener('input', render); $('topic').addEventListener('change', render); render();
  for (const [index, carousel] of data.carousels.entries()) {
    const details = element('details', undefined, 'asset');
    details.append(element('summary', `${String(index + 1).padStart(2, '0')} · ${carousel.title}`));
    const slides = element('ol'); for (const slide of carousel.slides) slides.append(element('li', slide)); details.append(slides);
    details.append(element('p', `Adapted from days ${carousel.days.join(', ')}. Six-slide outline; visual production pending.`, 'muted'));
    $('carousels').append(details);
  }
  for (const segment of data.video.segments) { const details = element('details'); details.append(element('summary', `${segment.time} · ${segment.visual}`), element('p', segment.voiceover)); $('video-script').append(details); }
  $('video-script').append(element('p', 'Timing is a production target. Confirm the final duration and add captions after recording.', 'muted'));
  for (const [key, label] of [['business','Business context'],['work','Technical work'],['result','Measured outcome and decision'],['architecture','Architectural decision'],['next','Next gate']]) {
    $('case-study').append(element('h3', label), element('p', data.caseStudy[key]));
  }
  media(data.media);
  for (const id of ['copy-brief', 'copy-bottom']) $(id).addEventListener('click', async () => {
    try { const response = await fetch('HARK_CAMPAIGN.md'); if (!response.ok) throw new Error(); await copy(await response.text(), $(id)); }
    catch { $('feedback').textContent = 'The brief could not be loaded. Use the download link or repository copy.'; }
  });
  if (location.hash.startsWith('#day-')) document.getElementById(location.hash.slice(1))?.scrollIntoView();
}
main().catch(() => { $('posts').replaceChildren(element('p', 'Campaign loading failed. Use the Markdown download above. Open this page through a web server rather than a file:// URL.')); });
