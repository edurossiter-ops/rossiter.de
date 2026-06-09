// Rossiter Consulting — comportamento + motion (filosofia Emil Kowalski)
(function(){
  var root = document.documentElement;
  root.classList.add('js'); // redundante (head já adiciona) — seguro

  // NAV scroll state
  var nav = document.getElementById('nav');
  if (nav) addEventListener('scroll', function(){ nav.classList.toggle('scrolled', scrollY > 20); }, {passive:true});

  // Menu mobile
  var burger = document.getElementById('burger'), mobile = document.getElementById('mobile');
  if (burger && mobile){
    burger.addEventListener('click', function(){ mobile.classList.toggle('open'); });
    mobile.querySelectorAll('a').forEach(function(a){ a.addEventListener('click', function(){ mobile.classList.remove('open'); }); });
  }

  // Form (Formspree, sem redirect)
  var form = document.querySelector('form[action*="formspree.io"]');
  if (form) form.addEventListener('submit', async function(e){
    e.preventDefault();
    try { var r = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{'Accept':'application/json'}});
      if (r.ok){ form.reset(); var ok = form.querySelector('.form__ok'); if (ok) ok.style.display = 'block'; } } catch(_){}
  });

  // Reduced motion: conteúdo já visível, nenhum reveal — encerra aqui.
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // ===== reveal-on-scroll (Emil): só esconde com JS; fallback garante visível =====
  function mark(el, delay){ el.classList.add('reveal'); if (delay) el.style.transitionDelay = delay + 'ms'; }

  // blocos isolados
  document.querySelectorAll('.section__head,.intro__img,.intro__text,.metodo__tese,.result-strip,.pq__list,.form,.contato__text')
    .forEach(function(el){ mark(el, 0); });

  // grupos com stagger (30-80ms entre itens)
  [['.comp','.comp__card'],['.roc','.roc__step'],['.stats','.stat'],['.mgrid','.mitem']].forEach(function(g){
    document.querySelectorAll(g[0]).forEach(function(group){
      group.querySelectorAll(g[1]).forEach(function(child, i){ mark(child, i * 60); });
    });
  });

  function countUp(n){
    var t = n.firstChild; if (!t) return;
    var target = parseInt(String(t.nodeValue).replace(/\D/g, ''), 10); if (isNaN(target)) return;
    var start = performance.now(), dur = 900;
    (function frame(now){
      var p = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - p, 3);
      t.nodeValue = String(Math.round(e * target));
      if (p < 1) requestAnimationFrame(frame); else t.nodeValue = String(target);
    })(performance.now());
  }
  function showStat(el){ var n = el.querySelector('.n'); if (n) countUp(n); }

  function reveal(el){ el.classList.add('is-in'); if (el.classList.contains('stat')) showStat(el); }

  var io = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function(entries){
        entries.forEach(function(en){ if (en.isIntersecting){ reveal(en.target); io.unobserve(en.target); } });
      }, {rootMargin:'0px 0px -8% 0px'})
    : null;

  var nodes = document.querySelectorAll('.reveal');
  if (io) nodes.forEach(function(el){ io.observe(el); });
  else nodes.forEach(reveal);

  // Fallback: revela o que sobrar após 1.6s (headless/sem-scroll/IO falho) — anti blank-section
  setTimeout(function(){
    document.querySelectorAll('.reveal:not(.is-in)').forEach(reveal);
  }, 1600);
})();
