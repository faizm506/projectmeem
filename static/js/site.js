/* =========================================================
   MEEM site script  |  site.js (landing + app)
   1 Setup  2 Loader  3 Reveal + counters  4 Menu + scroll  5 Cursor + magnets
   6 Hero scene  7 Arcade  8 Timeline  9 Slider  10 FAQ  11 Form
   ========================================================= */
(() => {
  'use strict';

  /* ---------- 1. SETUP ---------- */
  const $  = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  const root = document.documentElement;

  /* ---------- 2. LOADER ---------- */
  const hasLoader = !!$('.loader');
  if (hasLoader) document.body.classList.add('lock');
  let started = false;
  function start() {
    if (started) return;
    started = true;
    $('.loader') && $('.loader').classList.add('out');
    root.classList.add('ready');
    document.body.classList.remove('lock');
    initReveal();
    setTimeout(() => { $('.loader') && $('.loader').remove(); }, 1400);
    setTimeout(() => { layoutTimeline(); onScroll(); }, 120);
  }
  if (hasLoader) { addEventListener('load', () => setTimeout(start, reduce ? 0 : 1900)); setTimeout(start, 4500); }
  else start();

  /* ---------- 3. REVEAL + COUNTERS ---------- */
  function initReveal() {
    $$('.pagehead .wrap > *, .pgrid > *, .stats > *, .grid > .card').forEach((n, i) => { if (!n.hasAttribute('data-reveal')) { n.setAttribute('data-reveal', ''); n.style.setProperty('--d', Math.min(i, 8) * 0.05 + 's'); } });
    $$('[data-stagger]').forEach(g => [...g.children].forEach((c, i) => {
      c.setAttribute('data-reveal', ''); c.style.setProperty('--d', (i * 0.09) + 's');
    }));
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    $$('[data-reveal]').forEach(el => io.observe(el));
    const cio = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { countUp(e.target); cio.unobserve(e.target); }
    }), { threshold: 0.6 });
    $$('[data-count]').forEach(el => cio.observe(el));
  }
  function countUp(el) {
    const to = +el.dataset.count, pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
    const fmt = n => pre + Math.round(n).toLocaleString('en-IN') + suf;
    if (reduce) { el.textContent = fmt(to); return; }
    const t0 = performance.now();
    (function step(t) {
      const p = Math.min((t - t0) / 2200, 1);
      el.textContent = fmt(to * (1 - Math.pow(1 - p, 4)));
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }

  /* ---------- 4. MENU + SCROLL ---------- */
  const menu = $('#menu'), burger = $('#burger');
  function setMenu(open) {
    menu.classList.toggle('open', open);
    menu.setAttribute('aria-hidden', String(!open));
    burger.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('lock', open);
    if (open) $('#menuClose').focus();
  }
  burger.addEventListener('click', () => setMenu(true));
  $('#menuClose').addEventListener('click', () => setMenu(false));
  $$('a', menu).forEach(a => a.addEventListener('click', () => setMenu(false)));
  addEventListener('keydown', e => { if (e.key === 'Escape' && menu.classList.contains('open')) setMenu(false); });

  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const y = scrollY, h = root.scrollHeight - innerHeight;
      $('.nav').classList.toggle('scrolled', y > 30);
      $('.progress').style.transform = `scaleX(${h > 0 ? y / h : 0})`;
      if (!reduce) {
        const imp = $('.impact');
        if (imp) imp.style.setProperty('--py2', (imp.getBoundingClientRect().top * -0.08) + 'px');
      }
      updateTimeline();
      ticking = false;
    });
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', () => { layoutTimeline(); onScroll(); });

  /* ---------- 5. CURSOR + MAGNETS ---------- */
  const cur = $('.cursor');
  if (cur && fine && !reduce) {
    let x = 0, y = 0, tx = 0, ty = 0;
    addEventListener('mousemove', e => { tx = e.clientX; ty = e.clientY; cur.classList.add('show'); }, { passive: true });
    document.addEventListener('mouseleave', () => cur.classList.remove('show'));
    (function loop() { x += (tx - x) * 0.18; y += (ty - y) * 0.18; cur.style.transform = `translate3d(${x}px,${y}px,0)`; requestAnimationFrame(loop); })();
    $$('a,button,input,.win').forEach(el => {
      el.addEventListener('mouseenter', () => cur.classList.add('big'));
      el.addEventListener('mouseleave', () => cur.classList.remove('big'));
    });
    $$('.btn').forEach(b => {
      b.addEventListener('mousemove', e => {
        const r = b.getBoundingClientRect();
        b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.22}px,${(e.clientY - r.top - r.height / 2) * 0.3}px)`;
      });
      b.addEventListener('mouseleave', () => { b.style.transform = ''; });
    });
  }

  /* ---------- 6. HERO SCENE ---------- */
  (function heroScene() {
    const svg = $('#shopScene');
    if (!svg) return;
    const NS = 'http://www.w3.org/2000/svg';
    const GROUND = 488, DOOR = 240, SPEED = 92, LIFE = 13, BASE = 1.15, FLIGHT = 2.5, HOME = { x: 515, y: 240 };
    const PEOPLE = [
      { k: 'w', c: '#245A48', s: '#E3B48A', name: 'Amina', item: 'a linen abaya' },
      { k: 'm', c: '#F3E4CB', s: '#B97E52', beard: 1, name: 'Yusuf', item: 'a book of duas' },
      { k: 'w', c: '#173F32', s: '#8C5B3A', name: 'Maryam', item: 'rose water toner' },
      { k: 'cw', c: '#C99A3B', s: '#D9A87A', name: 'Noor', item: 'a bedtime storybook' },
      { k: 'm', c: '#245A48', s: '#E3B48A', name: 'Ibrahim', item: 'date syrup from a family farm' },
      { k: 'w', c: '#7A5640', s: '#C68E5E', name: 'Layla', item: 'a cotton hijab set' }
    ];
    const PLACES = ['Gaza', 'Yemen', 'Sudan'], THANKS = ['JazakAllah khair', 'Thank you', 'Barakah'], AMOUNTS = [24, 36, 18, 42, 30, 27];

    const el = (tag, attrs, parent) => {
      const e = document.createElementNS(NS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (parent) parent.appendChild(e);
      return e;
    };
    const ST = 'stroke="#173F32" stroke-opacity=".28"';
    const armPath = c => `<path d="M2 -62C8 -58 10 -48 8 -38L3 -38C4 -46 3 -54 -2 -60Z" fill="${c}" ${ST}/>`;
    const bagSvg = '<g class="bag" opacity="0"><path d="M-2 -34h16l2 22h-20z" fill="#C99A3B" ' + ST + '/><path d="M2 -34c0-8 8-8 8 0" fill="none" stroke="#173F32" stroke-width="1.8"/></g>';
    const legs = '<g class="legs"><ellipse class="f1" cx="-6" cy="-2" rx="5.5" ry="2.6" fill="#173F32"/><ellipse class="f2" cx="7" cy="-2" rx="5.5" ry="2.6" fill="#173F32"/></g>';
    const eyes = '<circle cx="5" cy="-80.5" r=".95" fill="#173F32"/><circle cx="9" cy="-80.5" r=".95" fill="#173F32"/><path d="M4.8 -76.6Q7.2 -74 9.8 -76.6" fill="none" stroke="#173F32" stroke-width="1" stroke-linecap="round"/>';
    function woman(c, s) {
      return legs + `<g class="body"><path d="M-17 -4C-15 -34 -13 -52 -10 -62C-6 -68 6 -68 10 -62C13 -52 15 -34 17 -4Z" fill="${c}" ${ST}/>
        <rect x="-11.5" y="-47" width="23" height="3.2" rx="1.6" fill="#C99A3B"/>
        <g class="arm">${armPath(c)}<circle cx="5.5" cy="-36" r="3.2" fill="${s}"/>${bagSvg}</g>
        <path d="M-13 -62C-17 -76 -14 -93 0 -95C14 -93 17 -76 13 -62C6 -59 -6 -59 -13 -62Z" fill="${c}" ${ST}/>
        <ellipse cx="3.5" cy="-79" rx="6.8" ry="7.8" fill="${s}"/>${eyes}</g>`;
    }
    function man(c, s, beard) {
      return legs + `<g class="body"><path d="M-14 -4C-15 -30 -15 -48 -13 -60C-9 -66 9 -66 13 -60C15 -48 15 -30 14 -4Z" fill="${c}" ${ST}/>
        <rect x="-1.4" y="-60" width="2.8" height="22" fill="#173F32" opacity=".16"/>
        <g class="arm">${armPath(c)}<circle cx="5.5" cy="-36" r="3.2" fill="${s}"/>${bagSvg}</g>
        <circle cx="1" cy="-76" r="10.5" fill="${s}"/>${beard ? '<path d="M-8.5 -73C-6 -63 8 -63 10.5 -73C6 -68.5 -4 -68.5 -8.5 -73Z" fill="#2b2a28" opacity=".75"/>' : ''}
        <path d="M-9.5 -78C-9.5 -92 11.5 -92 11.5 -78Z" fill="#FDF4E8" ${ST}/><path d="M-9.5 -79.5H11.5" stroke="#C99A3B" stroke-width="2"/>
        <circle cx="5" cy="-77" r=".95" fill="#173F32"/><circle cx="9" cy="-77" r=".95" fill="#173F32"/>${beard ? '' : '<path d="M4.8 -72.8Q7.2 -70.4 9.8 -72.8" fill="none" stroke="#173F32" stroke-width="1" stroke-linecap="round"/>'}</g>`;
    }
    const figure = p => p.k === 'w' ? woman(p.c, p.s) : p.k === 'm' ? man(p.c, p.s, p.beard) :
      p.k === 'cw' ? `<g transform="scale(.66)">${woman(p.c, p.s)}</g>` : `<g transform="scale(.66)">${man(p.c, p.s, 0)}</g>`;
    const parts = g => ({ f1: g.querySelector('.f1'), f2: g.querySelector('.f2'), body: g.querySelector('.body'), arm: g.querySelector('.arm'), bag: g.querySelector('.bag') });

    // customers
    const peopleG = $('#people');
    const custs = [0, 1, 2].map(i => {
      const g = el('g', { class: 'cust', opacity: 0 }, peopleG);
      el('ellipse', { cx: 0, cy: 1, rx: 17, ry: 4, fill: '#173F32', opacity: 0.16 }, g);
      return { g, fig: el('g', {}, g), off: i * 4.3, cycle: -1, dir: 1, i, p: PEOPLE[0], entered: false, launched: false, pt: null };
    });
    // the family
    const famG = $('#family');
    const fam = [
      { p: { k: 'w', c: '#245A48', s: '#E3B48A' }, x: 478, y: 286, s: 0.52, arm: -112 },
      { p: { k: 'cw', c: '#C99A3B', s: '#C68E5E' }, x: 497, y: 286, s: 0.52, arm: -150 },
      { p: { k: 'm', c: '#F3E4CB', s: '#B97E52', beard: 1 }, x: 552, y: 286, s: 0.52, arm: -22 }
    ].map(f => {
      f.g = el('g', {}, famG); f.g.innerHTML = figure(f.p); f.pt = parts(f.g); f.cur = 0; return f;
    });
    // effects pools
    const fx = $('#fx');
    const coins = [0, 1, 2].map(() => {
      const g = el('g', { opacity: 0 }, fx);
      const trail = Array.from({ length: 12 }, () => el('circle', { r: 1, fill: '#C99A3B', opacity: 0 }, g));
      const core = el('g', {}, g);
      el('circle', { r: 17, fill: 'url(#glow)' }, core);
      el('circle', { r: 8.5, fill: '#C99A3B', stroke: '#173F32', 'stroke-width': 2 }, core);
      el('circle', { r: 3, fill: '#FDF4E8' }, core);
      return { g, trail, core, t0: -1, hist: [], P: null };
    });
    const hearts = Array.from({ length: 10 }, (_, i) => {
      const u = el('use', { opacity: 0, fill: i % 2 ? '#245A48' : '#C99A3B' }, fx);
      u.setAttribute('href', '#heart');
      return { u, t0: -1, x: 0, y: 0, seed: 0, big: 1 };
    });
    const dots = Array.from({ length: 14 }, (_, i) => ({ c: el('circle', { r: 2.6, fill: i % 3 ? '#C99A3B' : '#245A48', opacity: 0 }, fx), t0: -1, vx: 0, vy: 0 }));

    const sun = $('#sun'), dusk = $('#dusk'), doorGlow = $('#doorGlow'), winL = $('#winGlowL'), winR = $('#winGlowR');
    const basket = $('#basket'), bubble = $('#bubble'), bubbleText = $('#bubbleText'), keeperArm = $('#keeperArm');
    const totalEl = $('#sceneTotal'), famEl = $('#sceneFam'), capEl = $('#sceneCap'), steps = $$('.scene-steps li');
    const story = { name: 'Amina', item: 'a linen abaya', place: 'Gaza' };
    let total = 0, shown = 0, fams = 0, launches = 0;
    let jumpUntil = -1, glowUntil = -1, keeperUntil = -1, basketAt = -1, bubbleAt = -1, stageUntil = -1;
    let light = 0.2, keeperAng = 0, lastText = '', lastStage = -1, lastTotalText = '', lastFamText = '';

    const point = (P, t) => {
      const u = 1 - t;
      return {
        x: u * u * u * P[0].x + 3 * u * u * t * P[1].x + 3 * u * t * t * P[2].x + t * t * t * P[3].x,
        y: u * u * u * P[0].y + 3 * u * u * t * P[1].y + 3 * u * t * t * P[2].y + t * t * t * P[3].y
      };
    };
    const ease = p => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
    const back = p => { const c = 1.9; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };

    function spawnHeart(t, x, y, delay) {
      const h = hearts.find(k => k.t0 < 0);
      if (h) { h.t0 = t + (delay || 0); h.x = x; h.y = y; h.seed = Math.random() * 6; }
    }
    function launch(t, bx, by) {
      const c = coins.find(k => k.t0 < 0);
      if (!c) return;
      c.t0 = t; c.hist = [];
      c.P = [{ x: bx, y: by }, { x: bx + (HOME.x - bx) * 0.25, y: Math.min(by, HOME.y) - 175 }, { x: HOME.x - (HOME.x - bx) * 0.12 - 10, y: 34 }, { x: HOME.x, y: HOME.y }];
      story.place = PLACES[launches++ % PLACES.length];
      keeperUntil = t + 1.8;
    }
    function arrive(t) {
      total += AMOUNTS[(launches + 5) % AMOUNTS.length]; fams++;
      jumpUntil = t + 1.5; glowUntil = t + 2.8; basketAt = t; bubbleAt = t; stageUntil = t + 3.6; light = 1;
      bubbleText.textContent = THANKS[fams % THANKS.length];
      for (let k = 0; k < 4; k++) spawnHeart(t, 470 + Math.random() * 92, 228 - Math.random() * 8, k * 0.12);
      dots.forEach((d, i) => { const a = (i / dots.length) * Math.PI * 2 + Math.random() * 0.4, v = 42 + Math.random() * 46; d.t0 = t; d.vx = Math.cos(a) * v; d.vy = Math.sin(a) * v - 30; });
    }

    function render(t) {
      /* customers */
      custs.forEach(c => {
        const local = t - c.off;
        if (local < 0) { c.g.setAttribute('opacity', 0); return; }
        const cyc = Math.floor(local / LIFE), u = local - cyc * LIFE;
        if (cyc !== c.cycle) {
          c.cycle = cyc; c.entered = false; c.launched = false;
          c.dir = (cyc + c.i) % 2 === 0 ? 1 : -1;
          c.p = PEOPLE[(cyc * 2 + c.i) % PEOPLE.length];
          c.fig.innerHTML = figure(c.p); c.pt = parts(c.fig);
        }
        const d = c.dir, xs = d > 0 ? -50 : 690, xe = d > 0 ? 700 : -50;
        const dA = Math.abs(DOOR - xs) / SPEED, dE = Math.abs(xe - DOOR) / SPEED, B = 0.7, I = 1.4, C = 0.8;
        let x = DOOR, a = 1, s = 1, dy = 0, walk = false, bag = 0;
        if (u < dA) { x = xs + (DOOR - xs) * (u / dA); walk = true; }
        else if (u < dA + B) {
          const k = (u - dA) / B; a = 1 - k; s = 1 - 0.1 * k; dy = -4 * k;
          if (!c.entered) { c.entered = true; story.name = c.p.name; story.item = c.p.item; }
        } else if (u < dA + B + I) { a = 0; }
        else if (u < dA + B + I + C) {
          const k = (u - dA - B - I) / C; a = k; s = 0.9 + 0.1 * k; dy = -4 * (1 - k); bag = 1;
          if (!c.launched) {
            c.launched = true; story.name = c.p.name;
            const sc = BASE * s;
            launch(t, DOOR + d * 7 * sc, GROUND - 26 * sc);
            spawnHeart(t, DOOR + d * 10, GROUND - 100, 0.15);
          }
        } else if (u < dA + B + I + C + dE) { x = DOOR + (xe - DOOR) * ((u - dA - B - I - C) / dE); walk = true; bag = 1; }
        else a = 0;
        const ph = t * 9 + c.i * 2, sw = Math.sin(ph), sc2 = BASE * s;
        const p = c.pt;
        if (p) {
          p.f1.setAttribute('cx', (-6 + (walk ? sw * 5 : 0)).toFixed(1)); p.f1.setAttribute('cy', (-2 - (walk ? Math.max(0, sw) * 2.4 : 0)).toFixed(1));
          p.f2.setAttribute('cx', (7 - (walk ? sw * 5 : 0)).toFixed(1)); p.f2.setAttribute('cy', (-2 - (walk ? Math.max(0, -sw) * 2.4 : 0)).toFixed(1));
          p.body.setAttribute('transform', `translate(0 ${walk ? (-Math.abs(sw) * 2.4).toFixed(2) : 0}) rotate(${walk ? (sw * 1.4).toFixed(2) : 0})`);
          p.arm.setAttribute('transform', `rotate(${walk ? (-sw * 15).toFixed(1) : 0} 2 -60)`);
          p.bag.setAttribute('opacity', bag);
        }
        c.g.setAttribute('transform', `translate(${x.toFixed(1)} ${(GROUND + dy).toFixed(1)}) scale(${(d * sc2).toFixed(3)} ${sc2.toFixed(3)})`);
        c.g.setAttribute('opacity', a.toFixed(2));
      });

      /* coins */
      let flying = false;
      coins.forEach(c => {
        if (c.t0 < 0) return;
        const p = (t - c.t0) / FLIGHT;
        if (p >= 1) { c.t0 = -1; c.g.setAttribute('opacity', 0); c.trail.forEach(k => k.setAttribute('opacity', 0)); arrive(t); return; }
        flying = true;
        const pt = point(c.P, ease(p));
        c.hist.push(pt); if (c.hist.length > 13) c.hist.shift();
        c.core.setAttribute('transform', `translate(${pt.x.toFixed(1)} ${pt.y.toFixed(1)}) scale(${(0.6 + Math.min(p * 5, 1) * 0.4 + Math.sin(p * Math.PI) * 0.25).toFixed(2)})`);
        c.trail.forEach((k, i) => {
          const h = c.hist[c.hist.length - 2 - i];
          if (!h) { k.setAttribute('opacity', 0); return; }
          k.setAttribute('cx', h.x.toFixed(1)); k.setAttribute('cy', h.y.toFixed(1));
          k.setAttribute('r', (7 - i * 0.5).toFixed(1)); k.setAttribute('opacity', (0.5 - i * 0.04).toFixed(2));
        });
        c.g.setAttribute('opacity', 1);
      });

      /* hearts and sparkles of joy (gold dots) */
      hearts.forEach(h => {
        if (h.t0 < 0) return;
        const p = (t - h.t0) / 1.6;
        if (p < 0) return;
        if (p >= 1) { h.t0 = -1; h.u.setAttribute('opacity', 0); return; }
        h.u.setAttribute('transform', `translate(${(h.x + Math.sin(p * 5 + h.seed) * 5).toFixed(1)} ${(h.y - 48 * p).toFixed(1)}) scale(${(0.7 + 0.7 * p).toFixed(2)})`);
        h.u.setAttribute('opacity', (Math.min(1, p * 6) * (1 - p)).toFixed(2));
      });
      dots.forEach(d => {
        if (d.t0 < 0) return;
        const p = (t - d.t0) / 1.1;
        if (p >= 1) { d.t0 = -1; d.c.setAttribute('opacity', 0); return; }
        const tt = p * 1.1;
        d.c.setAttribute('cx', (HOME.x + d.vx * tt).toFixed(1)); d.c.setAttribute('cy', (HOME.y + d.vy * tt + 90 * tt * tt).toFixed(1));
        d.c.setAttribute('opacity', (1 - p).toFixed(2));
      });

      /* the family celebrates */
      const jumping = t < jumpUntil;
      fam.forEach((f, i) => {
        const jp = jumping ? 1 - (jumpUntil - t) / 1.5 : 0;
        const up = jumping ? Math.abs(Math.sin(jp * Math.PI * 3 + i * 0.8)) * (i === 1 ? 9 : 5) : 0;
        const target = jumping ? f.arm + Math.sin(t * 12 + i) * (i === 1 ? 14 : 4) : 0;
        f.cur += (target - f.cur) * 0.2;
        f.pt.arm.setAttribute('transform', `rotate(${f.cur.toFixed(1)} 2 -60)`);
        f.g.setAttribute('transform', `translate(${f.x} ${(f.y - up + Math.sin(t * 1.6 + i) * 0.5).toFixed(2)}) scale(${f.s})`);
      });
      // basket of food and water appears at the door
      if (basketAt >= 0) {
        const p = (t - basketAt) / 3.2;
        if (p >= 1) { basketAt = -1; basket.setAttribute('opacity', 0); }
        else {
          const sc = back(Math.min(p * 5, 1)), op = p > 0.85 ? 1 - (p - 0.85) / 0.15 : 1;
          basket.setAttribute('transform', `translate(515 295) scale(${sc.toFixed(3)})`); basket.setAttribute('opacity', op.toFixed(2));
        }
      }
      if (bubbleAt >= 0) {
        const p = (t - bubbleAt) / 2.6;
        if (p >= 1) { bubbleAt = -1; bubble.setAttribute('opacity', 0); }
        else {
          const op = Math.min(p * 8, 1) * (p > 0.8 ? 1 - (p - 0.8) / 0.2 : 1);
          bubble.setAttribute('transform', `translate(515 ${(132 - 8 * p).toFixed(1)}) scale(${(0.8 + 0.2 * Math.min(p * 6, 1)).toFixed(2)})`); bubble.setAttribute('opacity', op.toFixed(2));
        }
      }
      // shopkeeper waves goodbye
      const kt = t < keeperUntil ? -150 + Math.sin(t * 11) * 14 : 0;
      keeperAng += (kt - keeperAng) * 0.15;
      keeperArm.setAttribute('transform', `rotate(${keeperAng.toFixed(1)} 350 396)`);

      /* sky: slow sun, golden hour, warm windows */
      const sp = (t % 120) / 120, edge = Math.min(1, sp * 8, (1 - sp) * 8);
      sun.setAttribute('transform', `translate(${(70 + 500 * sp).toFixed(1)} ${(122 - Math.sin(Math.PI * sp) * 62).toFixed(1)})`);
      sun.setAttribute('opacity', edge.toFixed(2));
      const duskAmt = Math.max(0, Math.min(1, (sp - 0.5) / 0.35)) * edge;
      dusk.setAttribute('opacity', (0.16 * duskAmt).toFixed(3));
      light += ((0.2 + duskAmt * 0.55) - light) * 0.012;
      const glow = Math.min(1, light);
      winL.setAttribute('opacity', glow.toFixed(2)); winR.setAttribute('opacity', glow.toFixed(2));
      doorGlow.setAttribute('opacity', (t < glowUntil ? 0.95 : 0.3 + duskAmt * 0.3).toFixed(2));

      /* story caption, step pills and counters */
      const st = flying ? 1 : (t < stageUntil ? 2 : 0);
      const text = st === 0 ? `${story.name} is picking up ${story.item}.` : st === 1 ? `A share of ${story.name}'s order is set aside.` : `A family in ${story.place} sits down to a warm meal.`;
      if (text !== lastText) {
        lastText = text; capEl.textContent = text; capEl.classList.remove('swap'); void capEl.offsetWidth; capEl.classList.add('swap');
      }
      if (st !== lastStage) { lastStage = st; steps.forEach((li, i) => li.classList.toggle('on', i === st)); }
      shown += (total - shown) * 0.1;
      const tt = '\u20b9' + Math.round(total - shown < 0.5 ? total : shown).toLocaleString('en-IN');
      if (tt !== lastTotalText) { lastTotalText = tt; totalEl.textContent = tt; }
      const ft = fams === 1 ? '1 family fed' : fams + ' families fed';
      if (ft !== lastFamText) { lastFamText = ft; famEl.textContent = ft; }
    }

    if (reduce) { total = 96; shown = 96; fams = 4; light = 0.5; render(7.2); return; }   // one calm still frame

    // gentle 3D tilt on desktop
    const wrap = $('#sceneWrap'), area = $('.hero2');
    if (fine && wrap && area) {
      area.addEventListener('mousemove', e => {
        const r = wrap.getBoundingClientRect();
        const x = (e.clientX - (r.left + r.width / 2)) / innerWidth, y = (e.clientY - (r.top + r.height / 2)) / innerHeight;
        wrap.style.setProperty('--ry', (x * 7).toFixed(2) + 'deg'); wrap.style.setProperty('--rx', (-y * 6).toFixed(2) + 'deg');
      });
      area.addEventListener('mouseleave', () => { wrap.style.setProperty('--ry', '0deg'); wrap.style.setProperty('--rx', '0deg'); });
    }

    let visible = true, last = performance.now(), clock = 0;
    new IntersectionObserver(es => { visible = es[0].isIntersecting; }, { threshold: 0.05 }).observe(svg);
    (function loop(now) {
      const dt = Math.min(now - last, 100) / 1000; last = now;
      if (visible && !document.hidden) { clock += dt; render(clock); }
      requestAnimationFrame(loop);
    })(last);
  })();

  /* ---------- 7. ARCADE: draggable 3D category carousel ---------- */
  const rig = $('#rig');
  if (rig) {
    const cyl = $('#cyl'), wins = $$('.win', cyl), n = wins.length, step = 360 / n;
    const cap = $('#cap'), capName = $('#capName'), capText = $('#capText'), capLink = $('#capLink'), dotsEl = $('#adots');
    let R = 300, angle = 0, target = 0, active = -1, dragging = false;
    let startX = 0, startA = 0, lastX = 0, lastT = 0, vel = 0, downWin = null;
    let hover = false, visible = false, lastTouch = 0, raf = 0;
    const mod = (a, m) => ((a % m) + m) % m;
    const k = () => step / (wins[0].offsetWidth * 0.9);
    const dots = wins.map((w, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.setAttribute('aria-label', 'Show ' + $('h3', w).textContent);
      b.addEventListener('click', () => { lastTouch = Date.now(); goTo(i); });
      dotsEl.appendChild(b); return b;
    });
    function layout() {
      const w = wins[0].offsetWidth;
      R = (w / 2) / Math.tan(Math.PI / n) + Math.max(18, w * 0.08);
      wins.forEach((el, i) => { el.style.transform = `rotateY(${i * step}deg) translateZ(${R}px)`; });
      kick();
    }
    function setActive(i) {
      if (i === active) return;
      const first = active === -1; active = i;
      wins.forEach((w, j) => w.classList.toggle('front', j === i));
      dots.forEach((d, j) => d.classList.toggle('on', j === i));
      capName.textContent = $('h3', wins[i]).textContent; capText.textContent = $('p', wins[i]).textContent;
      if (capLink && wins[i].dataset.url) capLink.setAttribute('href', wins[i].dataset.url);
      if (!first) { cap.classList.remove('swap'); void cap.offsetWidth; cap.classList.add('swap'); }
    }
    function frame() {
      if (!dragging) angle += (target - angle) * (reduce ? 1 : 0.085);
      cyl.style.transform = `translateZ(${-R}px) rotateY(${-angle}deg)`;
      setActive(mod(Math.round(angle / step), n));
      raf = (dragging || Math.abs(target - angle) > 0.02) ? requestAnimationFrame(frame) : 0;
    }
    function kick() { if (!raf) raf = requestAnimationFrame(frame); }
    function go(d) { target = (Math.round(target / step) + d) * step; kick(); }
    function goTo(i) { const cur = Math.round(target / step), diff = mod(i - cur + n / 2, n) - n / 2; target = (cur + diff) * step; kick(); }

    rig.addEventListener('pointerdown', e => {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      dragging = true; lastTouch = Date.now(); startX = lastX = e.clientX; startA = angle; vel = 0; lastT = performance.now();
      downWin = e.target.closest('.win'); rig.classList.add('drag');
      rig.setPointerCapture && rig.setPointerCapture(e.pointerId); kick();
    });
    rig.addEventListener('pointermove', e => {
      if (!dragging) return;
      const now = performance.now(), dt = Math.max(now - lastT, 1);
      angle = startA - (e.clientX - startX) * k();
      vel = 0.8 * vel + 0.2 * (-(e.clientX - lastX) * k() / dt); lastX = e.clientX; lastT = now;
    });
    const release = e => {
      if (!dragging) return;
      dragging = false; rig.classList.remove('drag');
      if (Math.abs(e.clientX - startX) < 6 && downWin) goTo(wins.indexOf(downWin));
      else { const fling = Math.max(-step * 1.5, Math.min(step * 1.5, vel * 260)); target = Math.round((angle + fling) / step) * step; }
      downWin = null; kick();
    };
    rig.addEventListener('pointerup', release); rig.addEventListener('pointercancel', release);
    rig.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); lastTouch = Date.now(); go(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); lastTouch = Date.now(); go(1); }
    });
    $('#aPrev').addEventListener('click', () => { lastTouch = Date.now(); go(-1); });
    $('#aNext').addEventListener('click', () => { lastTouch = Date.now(); go(1); });
    if (fine && !reduce) {
      rig.addEventListener('mouseenter', () => { hover = true; });
      rig.addEventListener('mouseleave', () => { hover = false; rig.style.removeProperty('--ox'); });
      rig.addEventListener('mousemove', e => { const r = rig.getBoundingClientRect(); rig.style.setProperty('--ox', ((e.clientX - r.left) / r.width - 0.5) * -120 + 'px'); });
    }
    if (!reduce) {
      new IntersectionObserver(es => { visible = es[0].isIntersecting; }, { threshold: 0.3 }).observe(rig);
      setInterval(() => { if (visible && !dragging && !hover && Date.now() - lastTouch > 5000 && !rig.matches(':focus-visible')) go(1); }, 3400);
    }
    addEventListener('resize', layout);
    document.fonts && document.fonts.ready.then(layout);
    layout();
  }

  /* ---------- 8. HOW IT WORKS TIMELINE ---------- */
  const steps = $('.steps'), stepEls = $$('.step'), path = $('.wave .prog'), desktop = matchMedia('(min-width:960px)');
  let L = 0, ys = [];
  function lenAtY(y) { let lo = 0, hi = L; for (let i = 0; i < 22; i++) { const m = (lo + hi) / 2; path.getPointAtLength(m).y < y ? lo = m : hi = m; } return lo; }
  function layoutTimeline() {
    if (!steps) return;
    if (!desktop.matches) { stepEls.forEach(s => { const d = $('.dot', s); d.style.left = ''; d.style.top = ''; }); return; }
    L = path.getTotalLength();
    const W = steps.offsetWidth, H = steps.offsetHeight;
    ys = stepEls.map(s => {
      const cy = (s.offsetTop + s.offsetHeight / 2) / H * 1000, pt = path.getPointAtLength(lenAtY(cy)), d = $('.dot', s);
      d.style.left = (pt.x / 1000 * W - s.offsetLeft - 9) + 'px'; d.style.top = (s.offsetHeight / 2 - 9) + 'px';
      return cy;
    });
  }
  function updateTimeline() {
    if (!steps) return;
    const r = steps.getBoundingClientRect(), vh = innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.6 - r.top) / r.height));
    steps.style.setProperty('--p', p);
    if (desktop.matches && L) {
      path.style.strokeDashoffset = 1 - lenAtY(p * 1000) / L;
      stepEls.forEach((s, i) => s.classList.toggle('on', p * 1000 >= ys[i] - 10));
    } else stepEls.forEach(s => s.classList.toggle('on', s.getBoundingClientRect().top < vh * 0.65));
  }
  desktop.addEventListener && desktop.addEventListener('change', () => { layoutTimeline(); onScroll(); });
  document.fonts && document.fonts.ready.then(() => { layoutTimeline(); onScroll(); });

  /* ---------- 9. DONATION SLIDER ---------- */
  const range = $('#amount');
  if (range) {
    const fill = $('#jarFill'), RATE = (+range.dataset.bps || 200) / 10000;
    const upd = () => {
      const v = +range.value;
      $('#amt').textContent = v; $('#don').textContent = (v * RATE).toFixed(2); $('#rate').textContent = (RATE * 100) + '%';
      fill.style.transform = `scaleY(${Math.max(0.06, v / +range.max)})`;
      range.style.setProperty('--fill', ((v - range.min) / (range.max - range.min) * 100) + '%');
    };
    range.addEventListener('input', upd); upd();
  }

  /* ---------- 10. FAQ ---------- */
  const items = $$('.faq-item');
  items.forEach(it => {
    const b = $('.q', it);
    b.addEventListener('click', () => {
      const open = !it.classList.contains('open');
      items.forEach(o => { o.classList.remove('open'); $('.q', o).setAttribute('aria-expanded', 'false'); });
      it.classList.toggle('open', open); b.setAttribute('aria-expanded', String(open));
    });
  });

  /* ---------- 11. WAITLIST FORM (simulated) ---------- */
  const form = $('#waitlist');
  form && form.addEventListener('submit', e => {
    e.preventDefault();
    const input = $('#email'), err = $('#err');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(input.value.trim())) {
      err.textContent = 'Please enter a valid email address.'; input.setAttribute('aria-invalid', 'true'); input.focus(); return;
    }
    err.textContent = ''; input.removeAttribute('aria-invalid');
    $('.cta').classList.add('done');            // TODO: send input.value to your backend or email tool here
  });

  /* ---------- 12. MISC ---------- */
  const yr = $('#year'); if (yr) yr.textContent = new Date().getFullYear();
  if (reduce) $$('svg').forEach(s => s.pauseAnimations && s.pauseAnimations());
  onScroll();
})();
