---
name: carrossel-vivo
description: >-
  Carrossel VIVO para Instagram em português: cada slide é um vídeo curto em loop (1080x1350, 4:5, 30 fps) com
  motion design feito por código (HyperFrames + GSAP), música e efeitos sonoros gerados por código (R$0, sem modelo
  de vídeo nem de música), tudo caindo na batida de 120 BPM, e uma música só que continua de um slide para o outro.
  Dois modos: (1) motion puro, sem imagem (bola laranja que atravessa todos os slides, palavras gigantes, régua de
  tempo); (2) com a foto do usuário recortada em camadas (fundo → palavra gigante → pessoa → cartões flutuando).
  Use quando o usuário pedir "carrossel", "carrossel vivo", "carrossel animado", "carrossel com motion",
  "post do Instagram que se mexe", ou quiser divulgar um vídeo ou produto em carrossel.
---

# CARROSSEL VIVO — motion design em carrossel, na batida, R$0

Ideia e método inspirados no vídeo do NextPhase (Jad M.H, "New VIRAL Carousels With Motion Graphics 0$ Turned It
Into a Skill"). Esta skill foi refeita do zero, em português, com música e efeitos gerados por código.

`CV` = pasta desta skill (ex.: `~/.claude/skills/carrossel-vivo`) · `PY` = Python 3 com `numpy` e `scipy`.
Também precisa: Node.js (para `npx hyperframes`) e FFmpeg. Exemplo pronto: `exemplo/claude-code-gratis/`.

## As 3 regras (o que separa bonito de barato)
1. **Easing** — nada anda em linha reta: `expo.out` para entrar, `power2.in` para cair, `back.out` para "pop".
2. **Peso** — a bola amassa ao tocar (`sq: true`), cai acelerando (`cai: true`), a palavra dá um "soco" na batida.
3. **Ritmo** — 120 BPM = 1 batida a cada 0,5 s; 1 compasso = 2 s. Todo evento cai numa batida (`CV.b(n)`), todo
   slide tem número INTEIRO de compassos. Senão o loop do Instagram dá um pulo no som.

## Ritmo padrão
- **Slide = 2 compassos = 4 s** (8 batidas), **5–7 slides**, UMA ideia por slide (gancho · prova · passo · número ·
  detalhe · CTA). Nada de slide longo com 3 ideias.
- O elemento principal entra até a batida 0,5; o resto até a batida 5; "arrasta →" na batida 6; saída em 7,75.
- Contador: ≤ 2 batidas para chegar e fica parado até o fim (≥ 1 s legível).
- Entrega já dividida: `postar/parte_01_de_06.mp4` … + `legenda.md` (o `--render` monta a pasta sozinho) e
  `carrossel_inteiro.mp4` só para conferir.

## Fluxo
1. **Plano** (mostrar ao usuário antes de produzir): tema, 5–7 slides — gancho, passos/prova, CTA. Só fatos reais
   do usuário (números, testes, hardware). Nunca inventar números. Terceiros sempre creditados.
2. **Projeto** `carrossel-<slug>/`: `carrossel.json` + `slides/sN.html` + `assets/` (fotos, recortes, quadros).
   Foto do usuário recortada sem fundo: `npx hyperframes remove-background foto.jpg -o recorte.png`.
   Quadros de vídeo com legenda queimada: recortar só a parte de cima (acima da legenda).
3. **Música + efeitos**: `$PY $CV/tools/musica.py <proj>` → `audio/slide_N.wav` + `musica_inteira.wav`.
   `sfx` por slide: `[batida, tipo]` com tipos `hit pop whoosh swoosh click tick shutter ding riser type thump`.
   `energia` 1–3 muda a bateria/arpejo. O rabo do som volta ao começo do slide (loop sem emenda).
4. **Conferir**: `$PY $CV/tools/montar.py <proj> --snap` → `work/snaps/sN/` (4 momentos por slide). Olhar todos:
   texto sobreposto, palavra cortada, bola em cima de número.
5. **Render**: `$PY $CV/tools/montar.py <proj> --render` (~1 min por slide) → `renders/slide_N.mp4`, `postar/`,
   `carrossel_inteiro.mp4` e `previa.html` (celular com setas, como arrastar). Conferir com ffprobe: 4,000 s,
   30 fps, 1080x1350, com áudio; volume ≈ −14 LUFS.
6. **Entregar**: a pasta `postar/` + legenda do post (`legenda.md`: gancho, 3 linhas, CTA, hashtags). No Instagram:
   novo post → selecionar os vídeos em ordem → carrossel.

## carrossel.json
```json
{ "titulo": "...", "topo": "TEXTO DA BARRA DE CIMA", "bpm": 120, "estilo": "tech",
  "slides": [ {"arquivo": "slides/s1.html", "compassos": 2, "energia": 3, "bola": true,
               "sfx": [[0, "hit"], [1.5, "pop"], [7.5, "swoosh"]]} ] }
```

## Como escrever um slide (`slides/sN.html` = só o miolo)
O `montar.py` já põe: fundo vivo, barra do topo (`topo` + "N/total"), régua de tempo (o tempo do carrossel
inteiro corre por baixo do cursor), a bola `#bola` (esconder com `"bola": false` no slide) e o áudio.
Classes: `.kicker` (serif itálico), `.big` / `.big.mid` / `.big.sm` (Anton gigante com gradiente), `.sub`, `.mono`,
`.tag` / `.tag.hot`, `.card` (borda ciano com brilho), `.term` (terminal), `.swipe` (canto de baixo), `.foot`.
Helpers (`CV`, com `tl` e `b()` soltos):
- `CV.split(sel)` + `CV.palavras(sel, batida, passo)` — palavra por palavra subindo da máscara.
- `CV.entra(sel, batida, from, dur, ease)` · `CV.pop(sel, batida)` · `CV.soco(sel, batida, escala)`.
- `CV.conta(sel, de, ate, batida, batidas, fmt)` — contador; termina ≥ 2 batidas antes do fim.
- `CV.digita(sel, texto, batida, letrasPorBatida)` — terminal.
- `CV.bola('#bola', [[batida, x, y, {cai, sq, ex, ey}], ...])` — centro da bola em px da página (1080x1350).
  Continuidade: a bola SAI pela direita no fim de um slide e ENTRA pela esquerda no começo do próximo.
- `CV.saida()` — tudo some na última meia batida, então o loop recomeça limpo. Sempre no fim do script.
Zona segura: conteúdo entre y 150 e y 1180 (a régua ocupa 1210–1280), margens de 64 px.

## Bugs que já aconteceram (checar sempre)
- Anton tem um espaço interno grande: `.big` já compensa com `display:block; margin-top:-.08em` + padding em cima
  (senão o acento de "GRÁTIS" é cortado pelo recorte do gradiente). Topo da letra ≈ `top` + 10 px.
- `CV.entra` com `yPercent` no `from` precisa zerar `yPercent` no destino (já zera) — sem isso a palavra fica
  70 % abaixo do lugar e cobre a linha de baixo.
- O tracinho maior da régua é `.tk.mj` (com `.big` ele batia com a palavra gigante).
- `<video>` dentro de cartão pode sair vazio no snapshot → usar quadro (jpg) no cartão.
- Não animar a `#bola` fora do `CV.bola` (o `CV.saida` não pode incluir a bola).
- Windows: prints com "→" quebram no cp1252 → texto ASCII nos prints.
