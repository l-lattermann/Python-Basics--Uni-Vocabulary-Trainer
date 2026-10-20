import hljs from './vendor/highlight-core.min.js';
import python from './vendor/hljs-python.min.js';
import bash from './vendor/hljs-bash.min.js';
import json from './vendor/hljs-json.min.js';

hljs.registerLanguage('python', python);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('json', json);

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const gap = html => html.replace(/___/g, '<span class="gap">___</span>');

// hljs leaves calls uncoloured; colour names followed by "(" outside other tokens, as an editor does.
function calls(html) {
  let depth = 0;
  return html.replace(/<\/?span[^>]*>|[^<]+/g, part => {
    if (part[0] === '<') {
      depth += part[1] === '/' ? -1 : 1;
      return part;
    }
    return depth ? part : part.replace(/\b([A-Za-z_]\w*)(?=\()/g, '<span class="hljs-title">$1</span>');
  });
}

marked.use({renderer: {
  code(code, info) {
    const language = (info || '').split(/\s/)[0];
    const lang = hljs.getLanguage(language);
    let html = lang ? hljs.highlight(code, {language}).value : esc(code);
    if (lang?.name === 'Python') html = calls(html);
    return `<pre><code>${gap(html)}</code></pre>`;
  },
  codespan: text => `<code>${gap(text)}</code>`,
}});
const md = s => s ? marked.parse(s) : '';
const mdi = s => s ? marked.parseInline(s) : '';

const ORIGINS = {generated: 'Kurs', 'knowledge-check': 'Knowledge check', 'outline-gap': 'Ergänzung'};
const MODES = [['mixed', 'Gemischt'], ['new', 'Nur neue Karten'], ['review', 'Nur wiederholen'], ['exam', 'Prüfungsmodus']];
const SESSION_SIZE = 50, NEW_PER_SESSION = 15, REPEAT_AFTER = 3;
const SCALES = [1, .94, .88, .82, .76, .7, .64, .58, .52, .46, .4];
const KEYS = {ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', ' ': 'space', Escape: 'esc',
  d: 'd', f: 'f', j: 'j', k: 'k', l: 'l'};

const root = document.getElementById('root');
const app = {view: 'start', deck: null, stats: null, current: null, warnings: [], msg: '', menu: 0, row: 0, filter: null, busy: false,
  pick: '', pickTop: 0, pickRows: Infinity, open: new Set()};
let sess = null;
let cur = null;

// Background writes: one request at a time, in order, retried until the server answers.
const net = {q: [], running: false, inflight: false, failed: false, waiters: []};
const seqBase = Date.now() * 1000;
let seqCount = 0;

function send(path, body) {
  net.q.push({path, body});
  pump();
}

async function pump() {
  if (net.running) return;
  net.running = true;
  let delay = 500;
  while (net.q.length) {
    const {path, body} = net.q[0];
    try {
      net.inflight = true;
      const r = await fetch(path, {method: 'POST', body: JSON.stringify(body), keepalive: true});
      net.inflight = false;
      if (r.status >= 500) throw new Error(`HTTP ${r.status}`);
      if (!r.ok) console.warn(path, body, await r.text());
      net.q.shift();
      delay = 500;
      setNet(false);
    } catch (error) {
      net.inflight = false;
      setNet(true);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, 8000);
    }
  }
  net.running = false;
  net.waiters.splice(0).forEach(resolve => resolve());
}

const drained = () => net.q.length ? new Promise(resolve => net.waiters.push(resolve)) : Promise.resolve();

function setNet(failed) {
  if (net.failed === failed) return;
  net.failed = failed;
  const el = document.querySelector('.net');
  if (el) el.textContent = netText();
}

const netText = () => net.failed ? `offline · ${net.q.length} ungesendet` : '';

addEventListener('pagehide', () => {
  const keep = net.inflight ? 1 : 0;
  for (const {path, body} of net.q.slice(keep)) navigator.sendBeacon(path, JSON.stringify(body));
  net.q.length = Math.min(net.q.length, keep);
});

async function post(path, body) {
  const r = await fetch(path, {method: 'POST', body: JSON.stringify(body)});
  return {ok: r.ok, data: await r.json()};
}

// Cards and sessions

function prep(card) {
  card.h = {
    q: md(card.question), a: md(card.answer), ex: md(card.explanation), add: md(card.addition),
    opts: (card.options || []).map(o => ({text: mdi(o.text), why: mdi(o.why)})),
    items: (card.items || []).map(mdi),
  };
  card.nCorrect = (card.options || []).filter(o => o.correct).length;
  return card;
}

function newSession(mode, number, cards, resumed) {
  sess = {mode, number, resumed, cards: {}, queue: cards.map(c => c.id), answered: 0, history: [], first: {}, up: 0, down: 0};
  for (const card of cards) sess.cards[card.id] = card.h ? card : prep(card);
  app.current = null;
}

function shuffle(list) {
  for (let i = list.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

function show(id) {
  const card = sess.cards[id];
  cur = {id, card, phase: 'q', cursor: 0, grab: false, picked: new Set(), flagging: false,
    pos: sess.answered + 1, total: sess.answered + sess.queue.length, repeat: id in sess.first};
  if (card.type === 'mc') cur.order = shuffle(card.options.map((_, i) => i));
  if (card.type === 'order') {
    do cur.order = shuffle(card.items.map((_, i) => i)); while (cur.order.every((v, i) => v === i));
  }
  app.view = 'card';
  preload();
  render();
}

function next() {
  if (sess.queue.length) return show(sess.queue[0]);
  cur = null;
  app.view = 'end';
  render();
}

function rate(correct) {
  const {id, card} = cur;
  const p = card.progress;
  sess.history.push({id, queue: sess.queue.slice(), answered: sess.answered, box: p.box, first: sess.first[id], up: sess.up, down: sess.down});
  if (!(id in sess.first)) {
    sess.first[id] = correct;
    const box = correct ? Math.min(p.box + 1, 5) : 1;
    if (correct && box > p.box) sess.up++;
    if (!correct && p.box > 1) sess.down++;
    card.progress = {...p, box};
  }
  sess.answered++;
  saveSession();
  sess.queue.shift();
  if (!correct) sess.queue.splice(Math.min(REPEAT_AFTER, sess.queue.length), 0, id);
  send('/api/rate', {id, correct, seq: seqBase + seqCount++});
}

function undo() {
  const h = sess.history.pop();
  if (!h) return serverUndo();
  const card = sess.cards[h.id];
  card.progress = {...card.progress, box: h.box};
  if (h.first === undefined) delete sess.first[h.id]; else sess.first[h.id] = h.first;
  Object.assign(sess, {answered: h.answered, up: h.up, down: h.down});
  saveSession();
  sess.queue = h.queue.filter(id => id === h.id || sess.cards[id].progress.flag == null);
  send('/api/undo', {});
  show(h.id);
}

async function serverUndo() {
  if (!sess.resumed) return;
  app.busy = true;
  await drained();
  const {ok, data} = await post('/api/undo', {});
  app.busy = false;
  if (!ok) {
    sess.resumed = false;
    return render();
  }
  const card = sess.cards[data.card.id] = prep(data.card);
  sess.queue = [card.id, ...sess.queue.filter(id => id !== card.id)];
  sess.answered = Math.max(0, sess.answered - 1);
  show(card.id);
}

function star() {
  const card = cur.card;
  card.progress = {...card.progress, starred: !card.progress.starred};
  send('/api/star', {id: card.id});
  render();
}

function saveFlag(note) {
  const card = cur.card;
  card.progress = {...card.progress, flag: note};
  sess.queue = sess.queue.filter(id => id !== card.id);
  send('/api/flag', {id: card.id, note});
  next();
}

const preloaded = new Map();
const images = card => ['question_images', 'answer_images', 'explanation_images', 'addition_images'].flatMap(k => card[k] || []);

function preload() {
  for (const id of sess.queue.slice(1, 4)) {
    for (const {src} of images(sess.cards[id])) {
      if (preloaded.has(src)) continue;
      const img = new Image();
      img.src = '/' + src;
      preloaded.set(src, img);
    }
  }
}

// Answer counts survive a reload so the end screen still covers the whole session.
function saveSession() {
  try {
    localStorage.setItem('session:' + app.deck.id, JSON.stringify({number: sess.number, first: sess.first, up: sess.up, down: sess.down, answered: sess.answered}));
  } catch {}
}

function restoreSession() {
  try {
    const saved = JSON.parse(localStorage.getItem('session:' + app.deck.id));
    if (saved?.number === sess.number) Object.assign(sess, saved);
  } catch {}
}

// Filter

function loadFilter() {
  let f = {};
  try {
    f = JSON.parse(localStorage.getItem('filter:' + app.deck.id)) || {};
  } catch {}
  const areas = Object.keys(app.deck.exam_areas || {});
  return {
    off: (f.off || []).filter(a => areas.includes(a)).slice(0, Math.max(areas.length - 1, 0)),
    sections: (Array.isArray(f.sections) ? f.sections : f.section ? [f.section] : []).filter(k => k in app.deck.sections),
    origin: f.origin in ORIGINS ? f.origin : '',
    starred: f.starred === true,
  };
}

function saveFilter() {
  try {
    localStorage.setItem('filter:' + app.deck.id, JSON.stringify(app.filter));
  } catch {}
}

const inSection = (section, prefix) => section === prefix || section.startsWith(prefix + '.');

function bySection(a, b) {
  const x = a.split('.').map(Number), y = b.split('.').map(Number);
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    if (x[i] !== y[i]) return (x[i] ?? -1) - (y[i] ?? -1);
  }
  return 0;
}

// Due and new counts for the current filter, where stats can tell; null where they cannot.
function scope() {
  const f = app.filter, s = app.stats;
  if (f.origin || f.starred || (f.off.length && f.sections.length)) return null;
  let parts;
  if (f.sections.length) parts = Object.entries(s.sections || {}).filter(([sec]) => f.sections.some(p => inSection(sec, p)));
  else if (f.off.length) parts = Object.entries(s.area_counts || {}).filter(([area]) => !f.off.includes(area));
  else return s;
  const out = {due: 0, new: 0, mastered: 0};
  for (const [, n] of parts) for (const k in out) out[k] += n[k];
  return out;
}

function apiFilter() {
  const f = app.filter, out = {};
  if (f.off.length) out.exam_areas = Object.keys(app.deck.exam_areas).filter(a => !f.off.includes(a));
  if (f.sections.length) out.sections = f.sections;
  if (f.origin) out.origins = [f.origin];
  if (f.starred) out.starred = true;
  return out;
}

function filterLabel() {
  const f = app.filter, areas = Object.keys(app.deck.exam_areas || {}).filter(a => !f.off.includes(a));
  const parts = [];
  if (areas.length) {
    parts.push(!f.off.length ? 'alle Bereiche' : areas.length > 2 ? `${areas.length} Bereiche`
      : areas.map(a => shortArea(app.deck.exam_areas[a].title)).join(', '));
  }
  if (f.origin) parts.push(ORIGINS[f.origin]);
  if (f.starred) parts.push('nur ★');
  return parts.join(' · ') || 'keiner';
}

const chapterLabel = () => !app.filter.sections.length ? 'alle'
  : app.filter.sections.length > 2 ? `${app.filter.sections.length} gewählt` : app.filter.sections.join(', ');

// Chapter tree: sections that hold cards themselves or below them, with subtree counts.
let tree = {};

function chapterTree() {
  if (tree.stats === app.stats) return tree;
  const counts = Object.entries(app.stats.sections || {});
  const keys = Object.keys(app.deck.sections).filter(k => counts.some(([sec]) => inSection(sec, k))).sort(bySection);
  const sum = {'': {total: 0, due: 0, new: 0}}, parent = {}, kids = {};
  for (const k of ['', ...keys]) {
    sum[k] = {total: 0, due: 0, new: 0};
    for (const [sec, n] of counts) {
      if (k === '' || inSection(sec, k)) for (const f in sum[k]) sum[k][f] += n[f];
    }
    if (k === '') continue;
    parent[k] = keys.filter(p => p !== k && inSection(k, p)).pop() || '';
    (kids[parent[k]] ||= []).push(k);
  }
  tree = {stats: app.stats, keys, sum, parent, kids};
  return tree;
}

const depth = k => k.split('.').length;
const isOpen = k => depth(k) === 1 || app.open.has(k);

function chapterRows() {
  const t = chapterTree();
  const visible = k => !t.parent[k] || (isOpen(t.parent[k]) && visible(t.parent[k]));
  return ['', ...t.keys.filter(visible)];
}

function toggleChapter(k) {
  const f = app.filter, t = chapterTree();
  const holder = f.sections.find(s => s !== k && inSection(k, s));
  if (k === '') f.sections = [];
  else if (f.sections.includes(k)) f.sections = f.sections.filter(s => s !== k);
  else if (holder) {
    // Unticking inside a ticked chapter: tick its other branches instead.
    f.sections = f.sections.filter(s => s !== holder);
    for (let at = holder; at !== k;) {
      const next = (t.kids[at] || []).find(c => inSection(k, c));
      if (!next) break;
      f.sections.push(...t.kids[at].filter(c => c !== next));
      at = next;
    }
  } else f.sections = [...f.sections.filter(s => !inSection(s, k)), k];
}

function shortArea(title) {
  const s = title.replace(/^(Implement|Develop|Build|Create)\s+/i, '')
    .replace(/\s+(an?\s+)?(Azure\s+AI\s+)?solutions?$/i, '').replace(/\s+and\s+/g, ' & ');
  return s[0].toUpperCase() + s.slice(1);
}

// Views

const kbd = ([keys, label, key]) => `<span class="keys-grp" data-key="${key}">${keys.map(k => `<kbd>${k}</kbd>`).join('')}<span class="klabel">${label}</span></span>`;
const footer = groups => `<footer class="keys">${groups.map(kbd).join('')}</footer>`;
const dots = box => [1, 2, 3, 4, 5].map(i => `<i class="${i <= box ? 'on' : ''}"></i>`).join('');
const num = n => n.toLocaleString('de-DE').replace(/\./g, '\u202f');
const count = (n, one, many) => `${num(n)} ${n === 1 ? one : many}`;
const weight = w => (w || '').replace(/(\d)\s*-\s*(\d+)\s*%/, '$1\u2013$2 %');
const host = url => esc(url.replace(/^https?:\/\//, ''));
const link = url => `<a href="${esc(url)}" target="_blank" rel="noopener">${host(url)}</a>`;

function header(left, right, share) {
  return `<header class="top"><div class="crumbs"><span class="deck">${esc(app.deck.id)}</span><span class="sep">·</span><span class="sec">${left}</span></div>
    <div class="status"><span class="net">${netText()}</span>${right}</div></header>
    <div class="progress"><i style="width:${(share * 100).toFixed(1)}%"></i></div>`;
}

function imgs(list, cls = '') {
  if (!list?.length) return '';
  return `<div class="imgs ${cls}">${list.map(({src, alt}) => {
    const pre = preloaded.get(src);
    const size = pre?.naturalWidth ? ` width="${pre.naturalWidth}" height="${pre.naturalHeight}"` : '';
    return `<img src="/${esc(src)}" alt="${esc(alt)}" title="${esc(alt)}"${size}>`;
  }).join('')}</div>`;
}

function resumable() {
  if (sess) return sess.queue.length;
  return app.current ? app.current.cards.filter(c => c.progress.flag == null).length : 0;
}

function menuItems() {
  const s = scope(), items = [], open = resumable();
  if (open) items.push({act: 'resume', what: 'Session fortsetzen', count: `${open} offen`});
  const fresh = s && Math.min(s.new, Math.max(NEW_PER_SESSION, SESSION_SIZE - s.due));
  const counts = s && {
    mixed: `${Math.min(s.due, SESSION_SIZE - fresh)} fällig + ${fresh} neu`,
    new: `${Math.min(s.new, SESSION_SIZE)} neu`,
    review: s.due > SESSION_SIZE ? `${SESSION_SIZE} von ${s.due} fällig` : `${s.due} fällig`,
    exam: `${s.mastered} sichere Karten`,
  };
  for (const [mode, what] of MODES) items.push({act: mode, what, count: s ? counts[mode] : ''});
  items.push({act: 'chapters', what: 'Kapitel: ' + chapterLabel(), count: 'wählen', cls: 'filter'});
  items.push({act: 'filter', what: 'Filter: ' + filterLabel(), count: 'ändern', cls: 'filter'});
  return items;
}

function startView() {
  const s = app.stats, deck = app.deck;
  const items = menuItems();
  app.menu = Math.min(app.menu, items.length - 1);
  const learned = Object.entries(s.boxes).reduce((sum, [box, n]) => sum + box * n, 0) / (5 * s.total || 1);
  const areas = Object.entries(deck.exam_areas || {}).map(([key, area]) => [area.title, area.weight, s.exam_areas[key], s.area_counts?.[key]]);
  if (!areas.length) areas.push(['Alle Karten', '', s.boxes, s]);
  return `<div class="app start">
    ${header(`Session ${s.session}`, '<span>Lernstand</span>', learned)}
    <main class="stage">
      <div class="title">${esc(deck.title)}</div>
      <div class="summary"><b>${num(s.total)}</b> Karten · <b>${num(s.due)}</b> fällig · <b>${num(s.new)}</b> neu · <b>${num(s.mastered)}</b> sicher · <b>${num(s.flagged)}</b> gemeldet</div>
      ${app.warnings.length ? `<div class="warn">${app.warnings.length} Hinweise beim Laden des Decks (siehe Terminal)</div>` : ''}
      ${app.msg ? `<div class="msg">${esc(app.msg)}</div>` : ''}
      <div class="cols">
        <div><h3>Session starten</h3><ul class="menu">${items.map((it, i) =>
          `<li class="${it.cls || ''} ${i === app.menu ? 'cursor' : ''}" data-i="${i}"><span class="what">${esc(it.what)}</span><span class="count">${esc(it.count)}</span></li>`).join('')}</ul></div>
        <div><h3>Nach Prüfungsbereich</h3><div class="areas">${areas.map(([title, w, boxes, n]) => {
          const total = Object.values(boxes).reduce((a, b) => a + b, 0);
          return `<div class="area-row"><div class="line"><span>${esc(title)}</span><span class="w">${esc(weight(w))}</span></div>
            <div class="bar">${[0, 1, 2, 3, 4, 5].map(b => `<i class="b${b}" style="width:${boxes[b] / (total || 1) * 100}%"></i>`).join('')}</div>
            <div class="nums">${n ? `${num(n.due)} fällig · ${num(n.new)} neu` : `${count(total, 'Karte', 'Karten')} · ${num(boxes[0])} neu`}</div></div>`;
        }).join('')}</div>
        <div class="legend"><span><i class="b0"></i>neu</span><span><i class="b1"></i>Box 1</span><span><i class="b2"></i>2</span><span><i class="b3"></i>3</span><span><i class="b4"></i>4</span><span><i class="b5"></i>sicher</span></div></div>
      </div>
    </main>
    ${footer([[['↑↓'], 'navigieren', 'down'], [['␣'], 'auswählen', 'space']])}
  </div>`;
}

function filterRows() {
  return [...Object.keys(app.deck.exam_areas || {}).map(key => ({kind: 'area', key})),
    {kind: 'origin'}, {kind: 'starred'}];
}

function filterView() {
  const f = app.filter, rows = filterRows();
  const row = (r, i) => {
    const cls = i === app.row ? 'cursor' : '';
    if (r.kind === 'area') {
      const on = !f.off.includes(r.key), area = app.deck.exam_areas[r.key];
      return `<li class="${cls} ${on ? '' : 'off'}" data-i="${i}"><span class="what"><span class="mark ${on ? 'on' : ''}"></span>${esc(area.title)}</span><span class="count">${esc(weight(area.weight))}</span></li>`;
    }
    if (r.kind === 'starred') {
      return `<li class="${cls}" data-i="${i}"><span class="what"><span class="mark ${f.starred ? 'on' : ''}"></span>Nur ★</span><span class="count"></span></li>`;
    }
    return `<li class="${cls}" data-i="${i}"><span class="what">Herkunft</span><span class="count">‹ ${esc(ORIGINS[f.origin] || 'alle')} ›</span></li>`;
  };
  const kind = rows[app.row].kind;
  const keys = [[['↑↓'], 'navigieren', 'down'],
    kind === 'origin' ? [['←→'], 'wechseln', 'right'] : [['␣'], 'an/aus', 'space'],
    [['Esc'], 'zurück', 'esc']];
  return `<div class="app filter">
    ${header('Filter', '', 0)}
    <main class="stage">
      <div class="title">Filter</div>
      <div class="summary">Gilt für jede neue Session · ${esc(filterLabel())}</div>
      <ul class="menu filters">${rows.map(row).join('')}</ul>
    </main>
    ${footer(keys)}
  </div>`;
}

function chaptersView() {
  const t = chapterTree(), f = app.filter, rows = chapterRows();
  const at = Math.max(0, rows.indexOf(app.pick));
  const n = Math.min(app.pickRows, rows.length);
  app.pickTop = Math.max(0, Math.min(app.pickTop, at, rows.length - n));
  if (at >= app.pickTop + n) app.pickTop = at - n + 1;
  const row = k => {
    const d = k ? depth(k) : 0, c = t.sum[k], hasKids = t.kids[k] && d > 1;
    const mark = k === '' ? (f.sections.length ? '' : 'on') : f.sections.includes(k) ? 'on'
      : f.sections.some(s => inSection(k, s)) ? 'cov' : f.sections.some(s => inSection(s, k)) ? 'part' : '';
    const what = k === '' ? 'Alle Kapitel'
      : `<span class="tw">${hasKids ? (isOpen(k) ? '▾' : '▸') : ''}</span><span class="num">${esc(k)}</span>${esc(app.deck.sections[k])}`;
    return `<li class="d${d} ${k === app.pick ? 'cursor' : ''}" data-i="${rows.indexOf(k)}" style="padding-left:${1 + Math.max(0, d - 1) * 1.6}rem">
      <span class="what"><span class="mark ${mark}"></span>${what}</span>
      <span class="count">${count(c.total, 'Karte', 'Karten')} · ${num(c.due)} fällig · ${num(c.new)} neu</span></li>`;
  };
  const cur = app.pick, keys = [[['↑↓'], 'navigieren', 'down'], [['␣'], 'an/aus', 'space']];
  if (cur && t.kids[cur] && depth(cur) > 1 && !app.open.has(cur)) keys.push([['→'], 'aufklappen', 'right']);
  if (cur && app.open.has(cur)) keys.push([['←'], 'zuklappen', 'left']);
  else if (cur && t.parent[cur]) keys.push([['←'], 'nach oben', 'left']);
  keys.push([['Esc'], 'fertig', 'esc']);
  const hidden = rows.length - app.pickTop - n;
  return `<div class="app chapters">
    ${header('Kapitel', '', 0)}
    <main class="stage">
      <div class="title">Kapitel wählen</div>
      <div class="summary">${f.sections.length ? `Gewählt: ${esc(f.sections.join(', '))}` : 'Alle Kapitel'} · ${count(f.sections.length ? t.keys.filter(k => f.sections.includes(k)).reduce((a, k) => a + t.sum[k].total, 0) : t.sum[''].total, 'Karte', 'Karten')}</div>
      <div class="more">${app.pickTop ? `▲ ${app.pickTop} weitere` : ''}</div>
      <ul class="menu tree">${rows.slice(app.pickTop, app.pickTop + n).map(row).join('')}</ul>
      <div class="more">${hidden > 0 ? `▼ ${hidden} weitere` : ''}</div>
    </main>
    ${footer(keys)}
  </div>`;
}

function cardKeys() {
  const {card, phase, grab} = cur;
  const tail = [[['K'], '★', 'k'], [['L'], 'melden', 'l'], [['Esc'], 'Menü', 'esc']];
  if (sess.history.length || sess.resumed) tail.unshift([['D'], 'zurück', 'd']);
  if (cur.flagging) return [[['↵'], 'speichern', 'enter'], [['Esc'], 'abbrechen', 'esc']];
  if (phase === 'r') {
    if (card.type !== 'basic') return [[['␣', '→'], 'weiter', 'space'], ...tail];
    return [[['←', 'F'], 'nicht gewusst', 'left'], [['→', 'J'], 'gewusst', 'right'], ...tail];
  }
  if (card.type === 'basic') return [[['␣'], 'aufdecken', 'space'], ...tail];
  if (card.type === 'mc') {
    if (card.nCorrect === 1) return [[['↑↓'], 'navigieren', 'down'], [['␣'], 'auswählen', 'space'], ...tail];
    return [[['↑↓'], 'navigieren', 'down'], [['␣'], 'an/aus', 'space'], [['→', 'J'], 'abgeben', 'right'], ...tail];
  }
  return [[['↑↓'], grab ? 'verschieben' : 'navigieren', 'down'], [['␣'], grab ? 'ablegen' : 'greifen', 'space'],
    [['→', 'J'], 'abgeben', 'right'], ...tail];
}

function optionsHtml() {
  const {card, phase} = cur;
  return `<ul class="options ${card.nCorrect > 1 ? 'multi' : 'single'}">${cur.order.map((oi, i) => {
    const o = card.options[oi], on = cur.picked.has(oi);
    const cls = phase === 'r' ? `${o.correct ? 'right' : on ? 'wrong' : ''} ${on ? 'on' : ''}`
      : `${on ? 'on' : ''} ${i === cur.cursor ? 'cursor' : ''}`;
    const why = phase === 'r' && card.h.opts[oi].why ? `<span class="why">${card.h.opts[oi].why}</span>` : '';
    return `<li class="opt ${cls}" data-i="${i}"><span class="mark"></span><span class="otext">${card.h.opts[oi].text}</span>${why}</li>`;
  }).join('')}</ul>`;
}

function itemsHtml() {
  const {card, phase} = cur;
  const list = `<ol class="items">${cur.order.map((ii, i) => {
    const cls = phase === 'r' ? (ii === i ? 'right' : 'wrong') : i === cur.cursor ? (cur.grab ? 'grab' : 'cursor') : '';
    return `<li class="item ${cls}" data-i="${i}"><span class="pos">${i + 1}</span><span class="grip">⋮⋮</span><span class="itext">${card.h.items[ii]}</span></li>`;
  }).join('')}</ol>`;
  if (phase === 'q') {
    return list + `<div class="hint">${cur.grab ? 'Ausgewählt — mit ↑↓ verschieben, Leertaste legt ab' : 'Leertaste greift den markierten Schritt'}</div>`;
  }
  if (cur.correct) return list;
  return list + `<div class="correct-order"><div class="label">Richtige Reihenfolge</div><ol>${card.h.items.map(t => `<li>${t}</li>`).join('')}</ol></div>`;
}

function answerHtml() {
  const card = cur.card, h = card.h;
  const ex = h.ex || card.explanation_images?.length
    ? `<div class="ex-wrap"><div class="explanation">${h.ex}</div>${card.explanation_images?.length ? `<div class="fig">${imgs(card.explanation_images)}</div>` : ''}</div>` : '';
  const add = h.add
    ? `<div class="addition"><div class="label">Addition</div><div class="add-text">${h.add}</div>${imgs(card.addition_images)}${card.addition_source ? `<div class="add-src">${link(card.addition_source)}</div>` : ''}</div>` : '';
  return `<section class="a">
    <div class="ans-wrap"><div class="answer"><div class="answer-main">${h.a}</div></div>${imgs(card.answer_images)}</div>
    ${ex}${add}
    ${card.source_url ? `<div class="src">${link(card.source_url)}</div>` : ''}
  </section>`;
}

function cardView() {
  const {card, phase} = cur, p = card.progress, deck = app.deck;
  const area = deck.exam_areas?.[card.exam_area];
  const type = card.type === 'basic' ? 'Karte' : card.type === 'order' ? 'Reihenfolge'
    : card.nCorrect > 1 ? `Mehrfachauswahl · wähle ${card.nCorrect}` : 'Multiple Choice';
  const right = `${area ? `<span class="area">${esc(shortArea(area.title))}</span>` : ''}<span class="boxdots" title="Box ${p.box}">${dots(p.box)}</span><span class="pos">${cur.pos} / ${cur.total}</span>`;
  return `<div class="app type-${card.type} ${phase === 'r' ? 'revealed' : ''}" data-card="${esc(card.id)}">
    ${header(`${esc(card.section)} ${esc(deck.sections[card.section])}`, right, (cur.pos - 1) / cur.total)}
    <main class="stage">
      <section class="q">
        <div class="meta"><span class="type">${type}</span><span class="origin o-${card.origin}">${ORIGINS[card.origin]}</span>${cur.repeat ? '<span>nochmal</span>' : ''}${p.starred ? '<span class="star">★</span>' : ''}</div>
        <div class="question">${card.h.q}</div>
        ${imgs(card.question_images)}
        ${card.type === 'mc' ? optionsHtml() : card.type === 'order' ? itemsHtml() : ''}
      </section>
      ${phase === 'r' ? answerHtml() : ''}
    </main>
    ${cur.flagging ? '<div class="flagbar"><span class="label">Melden</span><input id="note" maxlength="500" placeholder="Was stimmt mit der Karte nicht?" autocomplete="off"></div>' : ''}
    ${footer(cardKeys())}
  </div>`;
}

function endView() {
  const ids = Object.keys(sess.first), done = ids.length;
  const right = ids.filter(id => sess.first[id]).length;
  const keys = [[['␣'], 'Start', 'space']];
  if (sess.history.length) keys.push([['D'], 'zurück', 'd']);
  return `<div class="app end">
    ${header(`Session ${sess.number}`, `<span class="pos">${sess.answered} / ${sess.answered}</span>`, 1)}
    <main class="stage">
      <div class="title">Session fertig</div>
      <div class="summary">${count(sess.answered, 'Antwort', 'Antworten')}, davon ${count(sess.answered - done, 'Wiederholung', 'Wiederholungen')}</div>
      <div class="results">
        <div><b>${num(done)}</b><span>${done === 1 ? 'Karte' : 'Karten'}</span></div>
        <div><b>${done ? Math.round(right / done * 100) : 0} %</b><span>beim ersten Mal richtig</span></div>
        <div><b>${num(sess.up)}</b><span>aufgestiegen</span></div>
        <div><b>${num(sess.down)}</b><span>abgestiegen</span></div>
      </div>
      <div class="msg">Leertaste → Start</div>
    </main>
    ${footer(keys)}
  </div>`;
}

const VIEWS = {start: startView, filter: filterView, chapters: chaptersView, card: cardView, end: endView};

function render() {
  root.innerHTML = VIEWS[app.view]();
  if (app.view === 'chapters') fitTree();
  fit();
  if (cur?.flagging) document.getElementById('note').focus();
}

// The chapter list shows a window of rows around the cursor instead of shrinking the text.
function fitTree() {
  const stage = root.querySelector('.stage'), list = root.querySelector('.tree');
  document.documentElement.style.fontSize = '16px';
  if (stage.scrollHeight <= stage.clientHeight + 1 || list.children.length < 2) return;
  const step = list.children[1].getBoundingClientRect().top - list.children[0].getBoundingClientRect().top;
  const room = stage.getBoundingClientRect().bottom - list.getBoundingClientRect().top - list.nextElementSibling.offsetHeight;
  app.pickRows = Math.max(3, Math.floor((room + step - list.children[0].offsetHeight) / step));
  root.innerHTML = chaptersView();
}

function fit() {
  const stage = root.querySelector('.stage'), style = document.documentElement.style;
  for (const scale of SCALES) {
    style.fontSize = 16 * scale + 'px';
    const pres = stage.querySelectorAll('pre');
    if (stage.scrollHeight <= stage.clientHeight + 1 && [...pres].every(p => p.scrollWidth <= p.clientWidth + 1)) return;
  }
}

// Keys

function toStart() {
  cur = null;
  app.view = 'start';
  app.menu = 0;
  render();
  drained().then(() => fetch('/api/stats')).then(r => r.json()).then(stats => {
    app.stats = stats;
    if (app.view === 'start') render();
  });
}

async function startSession(mode) {
  app.busy = true;
  app.msg = '';
  await drained();
  const {ok, data} = await post('/api/session', {mode, filter: apiFilter()});
  app.busy = false;
  if (!ok || data.empty) {
    app.msg = !ok ? data.error : data.next_due_in == null ? 'Keine Karten für diese Auswahl.'
      : data.next_due_in === 0 ? 'Nichts für diesen Modus — es sind Wiederholungen fällig.'
      : `Nichts fällig — nächste Karte in ${data.next_due_in} ${data.next_due_in === 1 ? 'Session' : 'Sessions'}.`;
    return render();
  }
  newSession(mode, data.number, data.cards, false);
  next();
}

function startKey(key) {
  const items = menuItems();
  if (key === 'up') app.menu = Math.max(0, app.menu - 1);
  else if (key === 'down') app.menu = Math.min(items.length - 1, app.menu + 1);
  else if (key === 'space') {
    const act = items[app.menu].act;
    if (act === 'filter') {
      app.view = 'filter';
      app.row = 0;
    } else if (act === 'chapters') {
      Object.assign(app, {view: 'chapters', pick: '', pickTop: 0, pickRows: Infinity});
    } else if (act === 'resume') {
      if (!sess || !sess.queue.length) {
        const c = app.current;
        newSession(c.mode, c.number, c.cards.filter(card => card.progress.flag == null), true);
        restoreSession();
      }
      return next();
    } else return startSession(act);
  } else return;
  render();
}

function filterKey(key) {
  const rows = filterRows(), row = rows[app.row], f = app.filter;
  if (key === 'esc') {
    app.view = 'start';
    app.menu = menuItems().findIndex(it => it.act === 'filter');
  } else if (key === 'up') app.row = Math.max(0, app.row - 1);
  else if (key === 'down') app.row = Math.min(rows.length - 1, app.row + 1);
  else if (key === 'space' && row.kind === 'area') {
    const areas = Object.keys(app.deck.exam_areas);
    if (f.off.includes(row.key)) f.off = f.off.filter(a => a !== row.key);
    else if (f.off.length < areas.length - 1) f.off.push(row.key);
  } else if (key === 'space' && row.kind === 'starred') f.starred = !f.starred;
  else if ((key === 'left' || key === 'right') && row.kind === 'origin') {
    const values = ['', ...Object.keys(ORIGINS)];
    f.origin = values[(values.indexOf(f.origin) + (key === 'left' ? -1 : 1) + values.length) % values.length];
  } else return;
  saveFilter();
  render();
}

function chaptersKey(key) {
  const rows = chapterRows(), t = chapterTree(), k = app.pick, i = Math.max(0, rows.indexOf(k));
  if (key === 'esc') {
    app.view = 'start';
    app.menu = menuItems().findIndex(it => it.act === 'chapters');
    return render();
  }
  if (key === 'up') app.pick = rows[Math.max(0, i - 1)];
  else if (key === 'down') app.pick = rows[Math.min(rows.length - 1, i + 1)];
  else if (key === 'right' && k && t.kids[k] && depth(k) > 1) app.open.add(k);
  else if (key === 'left' && app.open.has(k)) app.open.delete(k);
  else if (key === 'left' && k) app.pick = t.parent[k];
  else if (key === 'space') {
    toggleChapter(k);
    saveFilter();
  } else return;
  render();
}

function cardKey(key) {
  const c = cur, card = c.card;
  if (key === 'esc') return toStart();
  if (key === 'd') return undo();
  if (key === 'k') return star();
  if (key === 'l') {
    c.flagging = true;
    return render();
  }
  if (c.phase === 'r') {
    if (card.type !== 'basic') return key === 'space' || key === 'right' || key === 'j' ? next() : undefined;
    if (key === 'left' || key === 'f') rate(false);
    else if (key === 'right' || key === 'j') rate(true);
    else return;
    return next();
  }
  if (card.type === 'basic') {
    if (key !== 'space') return;
    c.phase = 'r';
  } else if (card.type === 'mc') {
    const multi = card.nCorrect > 1;
    if (key === 'up') c.cursor = Math.max(0, c.cursor - 1);
    else if (key === 'down') c.cursor = Math.min(c.order.length - 1, c.cursor + 1);
    else if (key === 'space' && !multi) {
      c.picked = new Set([c.order[c.cursor]]);
      submit(card.options[c.order[c.cursor]].correct);
    } else if (key === 'space') {
      const oi = c.order[c.cursor];
      c.picked.has(oi) ? c.picked.delete(oi) : c.picked.add(oi);
    } else if ((key === 'right' || key === 'j') && multi && c.picked.size) {
      submit(card.options.every((o, i) => o.correct === c.picked.has(i)));
    } else return;
  } else {
    const o = c.order, i = c.cursor;
    if (key === 'up' || key === 'down') {
      const j = Math.min(o.length - 1, Math.max(0, i + (key === 'up' ? -1 : 1)));
      if (c.grab) [o[i], o[j]] = [o[j], o[i]];
      c.cursor = j;
    } else if (key === 'space') c.grab = !c.grab;
    else if (key === 'right' || key === 'j') {
      c.grab = false;
      submit(o.every((v, k) => v === k));
    } else return;
  }
  render();
}

function submit(correct) {
  cur.correct = correct;
  cur.phase = 'r';
  rate(correct);
}

function flagKey(e) {
  if (e.key === 'Escape') {
    cur.flagging = false;
    render();
  } else if (e.key === 'Enter') saveFlag(document.getElementById('note').value.trim());
  else return;
  e.preventDefault();
}

function handle(key) {
  if (app.busy || !app.deck) return;
  if (cur?.flagging) {
    if (key === 'esc' || key === 'enter') flagKey({key: key === 'esc' ? 'Escape' : 'Enter', preventDefault() {}});
    return;
  }
  if (app.view === 'start') startKey(key);
  else if (app.view === 'filter') filterKey(key);
  else if (app.view === 'chapters') chaptersKey(key);
  else if (app.view === 'card') cardKey(key);
  else if (key === 'space' || key === 'esc') {
    sess = null;
    toStart();
  } else if (key === 'd') undo();
}

addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (cur?.flagging) return flagKey(e);
  const key = KEYS[e.key.length === 1 ? e.key.toLowerCase() : e.key];
  if (!key) return;
  e.preventDefault();
  if (!e.repeat) handle(key);
});

root.addEventListener('click', e => {
  const group = e.target.closest('[data-key]');
  if (group) return handle(group.dataset.key);
  const el = e.target.closest('[data-i]');
  if (!el || app.busy) return;
  const i = Number(el.dataset.i);
  if (app.view === 'start') {
    app.menu = i;
    handle('space');
  } else if (app.view === 'filter') {
    app.row = i;
    handle(filterRows()[i].kind === 'origin' ? 'right' : 'space');
  } else if (app.view === 'chapters') {
    app.pick = chapterRows()[i];
    handle('space');
  } else if (cur && cur.phase === 'q' && !cur.flagging) {
    if (cur.card.type === 'order' && cur.grab && i !== cur.cursor) {
      const [moved] = cur.order.splice(cur.cursor, 1);
      cur.order.splice(i, 0, moved);
      cur.grab = false;
      cur.cursor = i;
      return render();
    }
    cur.cursor = i;
    handle('space');
  }
});

root.addEventListener('load', e => {
  if (e.target.tagName === 'IMG') fit();
}, true);
addEventListener('resize', () => {
  if (!app.deck) return;
  app.pickRows = Infinity;
  app.view === 'chapters' ? render() : fit();
});

const state = await (await fetch('/api/state')).json();
Object.assign(app, {deck: state.deck, stats: state.stats, current: state.current, warnings: state.warnings});
app.filter = loadFilter();
state.current?.cards.forEach(prep);
render();
