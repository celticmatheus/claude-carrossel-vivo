/* CARROSSEL VIVO — helpers GSAP. Tudo cai na batida: CV.b(n) = segundo da batida n (0 = início do slide).
   Regra do loop: o estado em t = fim tem que ser igual ao de t = 0 → tudo entra depois de 0 e sai antes do fim
   (CV.saida), e o fundo usa ciclos que fecham exatamente na duração do slide. */
(function () {
  const S = window.CV_SLIDE;                 // {i, total, compassos, bpm, inicio, total_s}
  const beat = 60 / S.bpm, D = S.compassos * 4 * beat;
  const tl = gsap.timeline({ paused: true });
  const $ = (q) => document.querySelector(q), $$ = (q) => [...document.querySelectorAll(q)];
  const CV = { tl, beat, D, S, $, $$ };
  CV.b = (n) => n * beat;

  /* fundo vivo, fechando o ciclo exatamente em D */
  CV.fundo = () => {
    const g = $$('.bg .glow');
    g.forEach((el, k) => {
      tl.fromTo(el, { x: 0, y: 0 }, { keyframes: [
        { x: k ? -180 : 220, y: k ? 140 : -120, duration: D / 2, ease: 'sine.inOut' },
        { x: 0, y: 0, duration: D / 2, ease: 'sine.inOut' }] }, 0);
    });
    if ($('.bg .grid')) tl.fromTo('.bg .grid', { x: 0, y: 0 }, { x: 90, y: 90, duration: D, ease: 'none' }, 0);
    if ($('.bg .sheen')) tl.fromTo('.bg .sheen', { xPercent: 0 }, { xPercent: 520, duration: D, ease: 'power1.inOut' }, 0);
  };

  /* barra do topo + régua: a régua mostra o tempo do CARROSSEL inteiro, o cursor anda só no trecho deste slide */
  CV.regua = (sel = '.ruler') => {
    const R = $(sel); if (!R) return;
    const px = 140;                                   // px por segundo
    const strip = document.createElement('div'); strip.className = 'abs'; strip.style.cssText = 'left:0;top:0;height:70px;';
    const t0 = S.inicio - 4, t1 = S.inicio + D + 4;
    for (let t = Math.ceil(t0 * 2) / 2; t <= t1; t += 0.5) {
      const x = (t - t0) * px, tk = document.createElement('div');
      tk.className = 'tk' + (t % 2 === 0 ? ' mj' : ''); tk.style.left = x + 'px'; strip.appendChild(tk);
      if (t % 2 === 0 && t >= 0) { const c = document.createElement('div'); c.className = 'tc'; c.style.left = x + 'px';
        c.textContent = '00:' + String(Math.floor(t)).padStart(2, '0'); strip.appendChild(c); }
    }
    R.appendChild(strip);
    const head = document.createElement('div'); head.className = 'head'; head.style.left = '540px'; R.appendChild(head);
    // a fita corre por baixo do cursor fixo no meio: posição = tempo global
    tl.fromTo(strip, { x: 540 - (S.inicio - t0) * px }, { x: 540 - (S.inicio + D - t0) * px, duration: D, ease: 'none' }, 0);
  };

  /* palavras: cada .m > .w sobe da máscara; at = batida de início, step = batidas entre palavras */
  CV.palavras = (sel, at, step = 0.5, dur = 0.55) => {
    $$(sel + ' .w').forEach((w, k) => tl.fromTo(w, { yPercent: 150, rotation: 4, filter: 'blur(8px)' },
      { yPercent: 0, rotation: 0, filter: 'blur(0px)', duration: dur, ease: 'expo.out' }, CV.b(at + k * step)));
  };
  /* quebra o texto de um elemento em .m > .w */
  CV.split = (sel) => $$(sel).forEach((el) => {
    el.innerHTML = el.textContent.trim().split(/\s+/).map((t) => `<span class="m"><span class="w">${t}</span></span>`).join(' ');
  });

  CV.entra = (sel, at, from = { y: 40, opacity: 0, filter: 'blur(10px)' }, dur = 0.5, ease = 'expo.out') =>
    tl.fromTo(sel, from, { y: 0, x: 0, yPercent: 0, xPercent: 0, scale: 1, rotation: 0, rotationX: 0, opacity: 1, filter: 'blur(0px)', duration: dur, ease }, CV.b(at));
  CV.pop = (sel, at) => tl.fromTo(sel, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.45, ease: 'back.out(2.4)' }, CV.b(at));
  CV.soco = (sel, at, s = 1.08) => tl.to(sel, { scale: s, duration: beat / 4, yoyo: true, repeat: 1, ease: 'power2.out' }, CV.b(at));

  /* tudo some na última meia batida → o loop recomeça limpo */
  CV.saida = (sel = '.cont', dur = 0.32) =>
    tl.to(sel, { opacity: 0, y: -30, filter: 'blur(12px)', duration: dur, ease: 'power2.in' }, D - dur - 0.02);

  /* contador (odômetro simples); fmt(v) → texto. Termine ≥ 2 batidas antes da saída (número ≥ 1 s parado). */
  CV.conta = (sel, de, ate, at, batidas, fmt = (v) => Math.round(v)) => {
    const el = $(sel), o = { v: de };
    tl.set(el, { textContent: fmt(de) }, 0);
    tl.to(o, { v: ate, duration: CV.b(batidas), ease: 'power3.out', onUpdate: () => (el.textContent = fmt(o.v)) }, CV.b(at));
  };

  /* digitação no terminal: n caracteres por batida */
  CV.digita = (sel, texto, at, porBatida = 8) => {
    const el = $(sel), o = { n: 0 };
    tl.set(el, { textContent: '' }, 0);
    tl.to(o, { n: texto.length, duration: CV.b(texto.length / porBatida), ease: 'none',
      onUpdate: () => (el.textContent = texto.slice(0, Math.round(o.n))) }, CV.b(at));
  };

  /* bola: caminho de pontos [batida, x, y, {sq: true = amassa ao tocar}] — anda com ease, amassa no impacto */
  CV.bola = (sel, pontos) => {
    const el = $(sel);
    tl.set(el, { x: pontos[0][1], y: pontos[0][2], scaleX: 1, scaleY: 1 }, 0);
    for (let k = 1; k < pontos.length; k++) {
      const [b0] = pontos[k - 1], [b1, x, y, op] = pontos[k];
      const dur = CV.b(b1 - b0), o = op || {};
      tl.to(el, { x, duration: dur, ease: o.ex || 'power2.inOut' }, CV.b(b0));
      tl.to(el, { y, duration: dur, ease: o.ey || (o.cai ? 'power2.in' : 'power2.inOut') }, CV.b(b0));
      if (o.sq) tl.to(el, { keyframes: [{ scaleX: 1.35, scaleY: 0.68, duration: 0.07 }, { scaleX: 0.9, scaleY: 1.12, duration: 0.1 },
        { scaleX: 1, scaleY: 1, duration: 0.12 }], ease: 'power2.out' }, CV.b(b1));
    }
  };

  CV.fim = () => { window.__timelines = window.__timelines || {}; window.__timelines['main'] = tl; };
  window.CV = CV;
})();
