// Source lisible — la version minifiée est générée dans assets/js/main.min.js (voir README)
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* Navigation : fond flouté au scroll */
  const nav = document.querySelector('.nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', scrollY > 10);
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Titre : effet de déchiffrement (le texte réel est déjà dans le HTML) */
  const h1 = document.querySelector('[data-scramble]');
  const typedEl = document.getElementById('typed');
  const startTyping = () => {
    if (!typedEl || reduce) return;
    const words = typedEl.dataset.words.split('|');
    let w = 0, i = words[0].length, del = true;
    const loop = () => {
      const word = words[w];
      typedEl.textContent = word.slice(0, i);
      if (!del && i < word.length) i++;
      else if (!del) { del = true; return setTimeout(loop, 1800); }
      else if (i > 0) i--;
      else { del = false; w = (w + 1) % words.length; }
      setTimeout(loop, del ? 35 : 75);
    };
    setTimeout(loop, 1800);
  };
  if (h1 && !reduce) {
    const text = h1.textContent, glyphs = '!<>-_\\/[]{}=+*^?#01';
    const q = [...text].map((c, i) => ({ c, end: 15 + i * 3 + Math.random() * 15 }));
    let f = 0;
    h1.setAttribute('aria-label', text);
    const scr = () => {
      let out = '', done = 0;
      q.forEach(x => {
        if (f >= x.end || x.c === ' ') { out += x.c; done++; }
        else out += glyphs[Math.random() * glyphs.length | 0];
      });
      h1.textContent = out;
      if (done < q.length) { f++; requestAnimationFrame(scr); } else startTyping();
    };
    scr();
  } else startTyping();

  /* Fond : réseau de points qui réagit au curseur */
  const cv = document.getElementById('net');
  if (cv) {
    const ctx = cv.getContext('2d');
    let W, H, nodes = [], mouse = { x: -999, y: -999 };
    const resize = () => {
      const d = Math.min(devicePixelRatio || 1, 2);
      W = innerWidth; H = innerHeight; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0);
      nodes = Array.from({ length: Math.round(Math.min(60, W / 22)) }, () => ({
        x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25
      }));
    };
    resize();
    addEventListener('resize', resize);
    addEventListener('pointermove', e => { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = ctx.fillStyle = '#ededf3';
      ctx.lineWidth = .6;
      nodes.forEach(n => {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
      });
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j], d = Math.hypot(a.x - b.x, a.y - b.y);
          if (d < 130) { ctx.globalAlpha = (1 - d / 130) * .16; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
        }
        const dm = Math.hypot(a.x - mouse.x, a.y - mouse.y);
        if (dm < 180) { ctx.globalAlpha = (1 - dm / 180) * .4; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke(); }
        ctx.globalAlpha = .4; ctx.beginPath(); ctx.arc(a.x, a.y, 1.3, 0, 6.28); ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (!reduce) requestAnimationFrame(draw);
    };
    draw();
  }

  /* Cartes : projecteur qui suit la souris + légère inclinaison 3D */
  document.querySelectorAll('.card, .stat').forEach(el => {
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      el.style.setProperty('--mx', x + 'px');
      el.style.setProperty('--my', y + 'px');
      if (fine && !reduce && el.classList.contains('card'))
        el.style.transform = `perspective(900px) rotateX(${(y / r.height - .5) * -5}deg) rotateY(${(x / r.width - .5) * 5}deg) translateY(-4px)`;
    });
    el.addEventListener('pointerleave', () => { el.style.transform = ''; });
  });

  /* Mini-grille d'activité décorative */
  const cells = document.getElementById('cells');
  if (cells) for (let i = 0; i < 78; i++) {
    const c = document.createElement('i');
    if (i > 20 && Math.random() > .12) { c.className = 'on'; c.style.animationDelay = i * 12 + 'ms'; }
    cells.appendChild(c);
  }

  /* Compteurs : la valeur finale est dans le HTML, on l'anime depuis 0 */
  const count = el => {
    if (reduce) return;
    const final = el.textContent, target = +el.dataset.count, pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
    const t0 = performance.now();
    const step = now => {
      const p = Math.min((now - t0) / 1600, 1), e = 1 - Math.pow(1 - p, 4);
      el.textContent = p < 1 ? pre + Math.round(target * e).toLocaleString('fr-FR') + suf : final;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  /* Apparition au scroll */
  const io = new IntersectionObserver(entries => entries.forEach(en => {
    if (!en.isIntersecting) return;
    const el = en.target, sibs = [...el.parentElement.children].filter(c => c.classList.contains('reveal'));
    el.style.transitionDelay = sibs.indexOf(el) * 90 + 'ms';
    el.classList.add('in');
    setTimeout(() => { el.style.transitionDelay = ''; }, 1400);
    el.querySelectorAll('[data-count]').forEach(count);
    io.unobserve(el);
  }), { threshold: .12 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();
