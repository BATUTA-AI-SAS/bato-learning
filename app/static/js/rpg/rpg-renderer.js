const VIRTUAL_W = 320;
const VIRTUAL_H = 240;
const GRID_W = 20;
const GRID_H = 15;

export class Renderer {
  constructor(canvas, tileset) {
    this.canvas = canvas;
    this.tileset = tileset;
    this.ctx = canvas.getContext("2d");
    this.tileGrid = null;
    this.tileSize = tileset.tileSize;

    canvas.width = VIRTUAL_W;
    canvas.height = VIRTUAL_H;
    canvas.style.imageRendering = "pixelated";

    this._fadeAlpha = 0;
    this._fadeColor = "black";
    this._animTime = 0;

    this.resize();
    this._resizeHandler = () => this.resize();
    window.addEventListener("resize", this._resizeHandler);
  }

  setRoom(tileGrid, palette) {
    this.tileGrid = tileGrid;
    this.tileset.generate(palette);
  }

  drawFrame(state) {
    const ctx = this.ctx;
    const ts = this.tileSize;
    const tileCanvas = this.tileset.getCanvas();

    ctx.clearRect(0, 0, VIRTUAL_W, VIRTUAL_H);

    if (!this.tileGrid) return;

    this._animTime++;

    for (let y = 0; y < GRID_H; y++) {
      for (let x = 0; x < GRID_W; x++) {
        const tileId = this.tileGrid[y]?.[x] ?? 0;
        const { sx, sy } = this.tileset.getTileCoords(tileId);
        ctx.drawImage(tileCanvas, sx, sy, ts, ts, x * ts, y * ts, ts, ts);
      }
    }

    if (state.objects) {
      for (const obj of state.objects) {
        const px = obj.x * ts;
        const py = obj.y * ts;

        if (obj.completed || (state.completedSlugs && state.completedSlugs.has(obj.slug))) {
          ctx.fillStyle = "rgba(0, 200, 0, 0.2)";
          ctx.fillRect(px, py, ts, ts);
        } else if (obj.locked) {
          ctx.fillStyle = "rgba(200, 0, 0, 0.2)";
          ctx.fillRect(px, py, ts, ts);
        } else if (obj.hasPuzzle) {
          const pulse = Math.sin(this._animTime * 0.08) * 0.3 + 0.5;
          ctx.strokeStyle = `rgba(220, 160, 0, ${pulse})`;
          ctx.lineWidth = 1;
          ctx.strokeRect(px + 0.5, py + 0.5, ts - 1, ts - 1);
        }
      }
    }

    if (state.npc) {
      const { sx, sy } = this.tileset.getCharSprite(state.npc.facing ?? 0, 0);
      ctx.drawImage(tileCanvas, sx, sy, ts, ts, state.npc.x * ts, state.npc.y * ts, ts, ts);
    }

    const frame = state.animFrame ?? 0;
    const { sx: psx, sy: psy } = this.tileset.getCharSprite(state.facing, frame);
    ctx.drawImage(tileCanvas, psx, psy, ts, ts, state.playerPos.x * ts, state.playerPos.y * ts, ts, ts);

    this._drawHud(ctx, state.hudData);

    if (this._fadeAlpha > 0) {
      ctx.fillStyle = this._fadeColor === "white"
        ? `rgba(255,255,255,${this._fadeAlpha})`
        : `rgba(0,0,0,${this._fadeAlpha})`;
      ctx.fillRect(0, 0, VIRTUAL_W, VIRTUAL_H);
    }
  }

  _drawHud(ctx, hud) {
    if (!hud) return;

    ctx.font = "8px monospace";

    if (hud.roomName) {
      const text = hud.roomName;
      const tw = ctx.measureText(text).width;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(2, 2, tw + 6, 12);
      ctx.fillStyle = "#fff";
      ctx.fillText(text, 5, 10);
    }

    if (hud.xp !== undefined) {
      const text = `XP: ${hud.xp}`;
      const tw = ctx.measureText(text).width;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(VIRTUAL_W - tw - 8, 2, tw + 6, 12);
      ctx.fillStyle = "#ffd700";
      ctx.fillText(text, VIRTUAL_W - tw - 5, 10);
    }
  }

  fadeToBlack(durationMs) {
    return this._animateFade(0, 1, durationMs, "black");
  }

  fadeFromBlack(durationMs) {
    return this._animateFade(1, 0, durationMs, "black");
  }

  flashWhite(durationMs) {
    return new Promise(resolve => {
      const half = durationMs / 2;
      this._animateFade(0, 0.8, half, "white").then(() => {
        this._animateFade(0.8, 0, half, "white").then(resolve);
      });
    });
  }

  _animateFade(from, to, durationMs, color) {
    this._fadeColor = color;
    return new Promise(resolve => {
      const start = performance.now();
      const step = () => {
        const elapsed = performance.now() - start;
        const t = Math.min(1, elapsed / durationMs);
        this._fadeAlpha = from + (to - from) * t;
        if (t < 1) {
          requestAnimationFrame(step);
        } else {
          this._fadeAlpha = to;
          resolve();
        }
      };
      requestAnimationFrame(step);
    });
  }

  resize() {
    const parent = this.canvas.parentElement || document.body;
    const maxW = parent.clientWidth;
    const maxH = parent.clientHeight || window.innerHeight;
    const scaleX = maxW / VIRTUAL_W;
    const scaleY = maxH / VIRTUAL_H;
    const scale = Math.max(1, Math.floor(Math.min(scaleX, scaleY)));
    this.canvas.style.width = `${VIRTUAL_W * scale}px`;
    this.canvas.style.height = `${VIRTUAL_H * scale}px`;
    this.scale = scale;
  }

  destroy() {
    window.removeEventListener("resize", this._resizeHandler);
  }
}
