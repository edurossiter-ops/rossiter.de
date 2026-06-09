/* Rossiter v3 — hero field + scroll choreography */
(function () {
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function showAll() { document.querySelectorAll('.reveal').forEach(function (e) { e.style.opacity = 1; e.style.transform = 'none'; }); }

  var nav = document.getElementById('nav');
  function onScroll(y) { if (nav) nav.classList.toggle('solid', y > 40); }

  /* ===== Canvas convergence field ===== */
  var canvas = document.getElementById('field');
  if (canvas && canvas.getContext) {
    var ctx = canvas.getContext('2d'), W, H, DPR, nodes = [], px, py, mouse = { x: -1e4, y: -1e4 };
    function resize() {
      DPR = Math.min(2, window.devicePixelRatio || 1);
      W = canvas.clientWidth; H = canvas.clientHeight;
      canvas.width = W * DPR; canvas.height = H * DPR; ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      px = W * 0.7; py = H * 0.45;
    }
    function init() {
      resize();
      var n = Math.round(Math.min(90, Math.max(36, (W * H) / 22000))); nodes = [];
      for (var i = 0; i < n; i++) nodes.push({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25 });
    }
    function step() {
      ctx.clearRect(0, 0, W, H);
      var g = ctx.createRadialGradient(px, py, 0, px, py, 160);
      g.addColorStop(0, 'rgba(184,232,255,0.20)'); g.addColorStop(1, 'rgba(184,232,255,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, 160, 0, 7); ctx.fill();
      for (var i = 0; i < nodes.length; i++) {
        var a = nodes[i], dx = px - a.x, dy = py - a.y, d = Math.hypot(dx, dy) || 1;
        a.vx += (dx / d) * .004; a.vy += (dy / d) * .004;
        var mdx = a.x - mouse.x, mdy = a.y - mouse.y, md = Math.hypot(mdx, mdy);
        if (md < 120) { a.vx += (mdx / (md || 1)) * .5; a.vy += (mdy / (md || 1)) * .5; }
        a.vx *= .96; a.vy *= .96; a.x += a.vx; a.y += a.vy;
        if (a.x < 0 || a.x > W) a.vx *= -1; if (a.y < 0 || a.y > H) a.vy *= -1;
        if (d < 230) { ctx.strokeStyle = 'rgba(58,114,200,' + (.10 * (1 - d / 230)) + ')'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(px, py); ctx.stroke(); }
        for (var j = i + 1; j < nodes.length; j++) {
          var b = nodes[j], lx = a.x - b.x, ly = a.y - b.y, ld = Math.hypot(lx, ly);
          if (ld < 110) { ctx.strokeStyle = 'rgba(74,120,168,' + (.18 * (1 - ld / 110)) + ')'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
        }
        ctx.fillStyle = 'rgba(110,188,248,0.8)'; ctx.beginPath(); ctx.arc(a.x, a.y, 1.6, 0, 7); ctx.fill();
      }
      ctx.fillStyle = '#b8e8ff'; ctx.beginPath(); ctx.arc(px, py, 4, 0, 7); ctx.fill();
    }
    addEventListener('resize', resize, { passive: true });
    addEventListener('pointermove', function (e) { var r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; }, { passive: true });
    init();
    if (reduce) step(); else (function loop() { step(); requestAnimationFrame(loop); })();
  }

  var hasGsap = !!window.gsap, hasST = hasGsap && !!window.ScrollTrigger;

  /* contact form (Formspree) + newsletter (HubSpot pendente) */
  function wireForms() {
    var cf = document.querySelector('form[action*="formspree.io"]');
    if (cf) cf.addEventListener('submit', async function (e) {
      e.preventDefault();
      try { var r = await fetch(cf.action, { method: 'POST', body: new FormData(cf), headers: { 'Accept': 'application/json' } }); if (r.ok) { cf.reset(); var ok = cf.querySelector('.form__ok'); if (ok) ok.style.display = 'block'; } } catch (_) { }
    });
    var nf = document.getElementById('newsForm');
    if (nf) nf.addEventListener('submit', async function (e) {
      e.preventDefault();
      var input = nf.querySelector('input[type=email]'), btn = nf.querySelector('button');
      var email = input ? input.value.trim() : ''; if (!email) return;
      if (btn) { btn.disabled = true; btn.textContent = '...'; }
      var endpoint = 'https://forms-eu1.hsforms.com/submissions/v3/integration/submit/148665264/71c42ccf-ac88-49a2-bff9-fe9dca2b2c8d';
      try {
        var res = await fetch(endpoint, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fields: [{ objectTypeId: '0-1', name: 'email', value: email }], context: { pageUri: location.href, pageName: document.title } })
        });
        nf.innerHTML = res.ok
          ? '<p style="color:var(--sky);font-size:.95rem">Pronto. Você está inscrito.</p>'
          : '<p style="color:var(--sky);font-size:.95rem">Recebido. Se não confirmar, escreva para eduardo@rossiter.de.</p>';
      } catch (_) {
        nf.innerHTML = '<p style="color:var(--sky);font-size:.95rem">Recebido. Se não confirmar, escreva para eduardo@rossiter.de.</p>';
      }
    });
  }
  wireForms();

  if (reduce || !hasGsap) { showAll(); addEventListener('scroll', function () { onScroll(scrollY); }, { passive: true }); return; }
  if (hasST) gsap.registerPlugin(ScrollTrigger);

  /* Lenis smooth scroll + GSAP ticker */
  if (window.Lenis) {
    var lenis = new Lenis({ duration: 1.1, smoothWheel: true });
    lenis.on('scroll', function (e) { onScroll(e.scroll || scrollY); if (hasST) ScrollTrigger.update(); });
    gsap.ticker.add(function (t) { lenis.raf(t * 1000); }); gsap.ticker.lagSmoothing(0);
  } else { addEventListener('scroll', function () { onScroll(scrollY); if (hasST) ScrollTrigger.update(); }, { passive: true }); }

  /* Hero entrance */
  gsap.to('.hero .reveal', { opacity: 1, y: 0, stagger: .12, duration: .9, ease: 'power3.out', delay: .15 });

  if (!hasST) { showAll(); return; }

  /* Below-fold reveals */
  gsap.utils.toArray('.reveal').forEach(function (el) {
    if (el.closest('.hero')) return;
    gsap.to(el, { opacity: 1, y: 0, duration: .8, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 86%' } });
  });

  /* ROC pin + scrub */
  var roc = document.querySelector('.roc');
  if (roc && matchMedia('(min-width:781px)').matches) {
    var lets = roc.querySelectorAll('.let'), steps = roc.querySelectorAll('.roc__step'), bar = roc.querySelector('.roc__prog i'), last = -1;
    gsap.set(steps, { opacity: 0, y: 18 }); gsap.set(steps[0], { opacity: 1, y: 0 });
    ScrollTrigger.create({
      trigger: roc, start: 'top top', end: 'bottom bottom', scrub: true,
      onUpdate: function (self) {
        if (bar) bar.style.width = (self.progress * 100) + '%';
        var idx = Math.min(2, Math.floor(self.progress * 2.999));
        if (idx !== last) {
          last = idx;
          lets.forEach(function (l, i) { l.classList.toggle('on', i === idx); });
          steps.forEach(function (s, i) { gsap.to(s, { opacity: i === idx ? 1 : 0, y: i === idx ? 0 : 18, duration: .35, ease: 'power2.out' }); });
        }
      }
    });
  }

  /* Count-up */
  gsap.utils.toArray('.stat .n').forEach(function (n) {
    var target = +n.getAttribute('data-count'); if (!target) return;
    ScrollTrigger.create({
      trigger: n, start: 'top 88%', once: true, onEnter: function () {
        var o = { v: 0 }; gsap.to(o, { v: target, duration: 1.1, ease: 'power2.out', onUpdate: function () { n.firstChild.nodeValue = Math.round(o.v); } });
      }
    });
  });

  /* Parallax prova bg */
  var bg = document.getElementById('provaBg');
  if (bg) gsap.to(bg, { yPercent: -16, ease: 'none', scrollTrigger: { trigger: '.prova', start: 'top bottom', end: 'bottom top', scrub: true } });

  /* failsafe: if ScrollTrigger somehow didn't reveal above-fold items quickly */
  setTimeout(function () { document.querySelectorAll('.reveal').forEach(function (e) { var r = e.getBoundingClientRect(); if (r.top < innerHeight && getComputedStyle(e).opacity === '0') { e.style.opacity = 1; e.style.transform = 'none'; } }); }, 1500);
})();
