const TILE_COLS = 4;
const CHAR_COLS = 4;
const CHAR_ROWS = 2;

export const TileId = {
  FLOOR: 0,
  WALL: 1,
  DOOR_OPEN: 2,
  DOOR_LOCKED: 3,
  DESK: 4,
  TERMINAL: 5,
  BOOKSHELF: 6,
  SERVER_RACK: 7,
  WINDOW: 8,
  NPC_MARKER: 9,
  FLOOR_ALT: 10,
  RUG: 11,
  PLANT: 12,
  BOARD: 13,
  CHAIR: 14,
  STAIRS: 15,
};

export const Facing = { DOWN: 0, UP: 1, LEFT: 2, RIGHT: 3 };

export class Tileset {
  constructor(tileSize = 16) {
    this.tileSize = tileSize;
    this.canvas = null;
    this.tileCount = 16;
  }

  generate(palette) {
    const ts = this.tileSize;
    const cols = TILE_COLS;
    const rows = Math.ceil(this.tileCount / cols);
    const charRowsNeeded = CHAR_ROWS;
    const totalRows = rows + charRowsNeeded;

    this.canvas = document.createElement("canvas");
    this.canvas.width = cols * ts;
    this.canvas.height = totalRows * ts;
    const ctx = this.canvas.getContext("2d");

    this._drawTiles(ctx, palette, ts, cols);
    this._drawCharSprites(ctx, palette, ts, cols, rows);
  }

  _drawTiles(ctx, palette, ts, cols) {
    const painters = [
      this._drawFloor,
      this._drawWall,
      this._drawDoorOpen,
      this._drawDoorLocked,
      this._drawDesk,
      this._drawTerminal,
      this._drawBookshelf,
      this._drawServerRack,
      this._drawWindow,
      this._drawNpcMarker,
      this._drawFloorAlt,
      this._drawRug,
      this._drawPlant,
      this._drawBoard,
      this._drawChair,
      this._drawStairs,
    ];

    for (let i = 0; i < painters.length; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const ox = col * ts;
      const oy = row * ts;
      ctx.save();
      ctx.translate(ox, oy);
      painters[i].call(this, ctx, palette, ts);
      ctx.restore();
    }
  }

  _drawFloor(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
  }

  _drawWall(ctx, p, ts) {
    ctx.fillStyle = p.wall;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = this._darken(p.wall, 40);
    ctx.fillRect(1, ts - 1, ts - 1, 1);
    ctx.fillRect(ts - 1, 1, 1, ts - 1);
  }

  _drawDoorOpen(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#3a3";
    ctx.beginPath();
    ctx.moveTo(2, 6);
    ctx.quadraticCurveTo(ts / 2, 1, ts - 2, 6);
    ctx.lineTo(ts - 2, 8);
    ctx.quadraticCurveTo(ts / 2, 3, 2, 8);
    ctx.fill();
  }

  _drawDoorLocked(ctx, _p, ts) {
    ctx.fillStyle = "#333";
    ctx.fillRect(0, 0, ts, ts);
    ctx.strokeStyle = "#a22";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(3, 3);
    ctx.lineTo(ts - 3, ts - 3);
    ctx.moveTo(ts - 3, 3);
    ctx.lineTo(3, ts - 3);
    ctx.stroke();
  }

  _drawDesk(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#6b4226";
    ctx.fillRect(2, 6, ts - 4, ts - 8);
    ctx.fillStyle = "#8b5e3c";
    ctx.fillRect(2, 6, ts - 4, 2);
  }

  _drawTerminal(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(3, 4, ts - 6, ts - 6);
    ctx.fillStyle = "#0f0";
    ctx.fillRect(5, 6, ts - 10, ts - 10);
  }

  _drawBookshelf(ctx, p, ts) {
    ctx.fillStyle = p.wall;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#5c3317";
    ctx.fillRect(2, 3, ts - 4, ts - 4);
    const spineColors = ["#c44", "#48c", "#4a4", "#cc4"];
    for (let i = 0; i < 4; i++) {
      ctx.fillStyle = spineColors[i];
      ctx.fillRect(4 + i * 2, 4, 1, ts - 6);
    }
  }

  _drawServerRack(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#2a2a2a";
    ctx.fillRect(3, 2, ts - 6, ts - 4);
    ctx.fillStyle = "#0f0";
    ctx.fillRect(5, 5, 2, 2);
    ctx.fillRect(5, 9, 2, 2);
    ctx.fillRect(5, 13, 2, 2);
  }

  _drawWindow(ctx, p, ts) {
    ctx.fillStyle = p.wall;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#667b99";
    ctx.fillRect(3, 3, ts - 6, ts - 6);
  }

  _drawNpcMarker(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = p.accent;
    ctx.beginPath();
    ctx.arc(ts / 2, ts / 2, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  _drawFloorAlt(ctx, p, ts) {
    ctx.fillStyle = this._darken(p.floor, 10);
    ctx.fillRect(0, 0, ts, ts);
  }

  _drawRug(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.globalAlpha = 0.4;
    ctx.fillStyle = p.accent;
    ctx.fillRect(1, 1, ts - 2, ts - 2);
    ctx.globalAlpha = 1;
  }

  _drawPlant(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#5c3317";
    ctx.fillRect(6, 10, 4, 5);
    ctx.fillStyle = "#2a2";
    ctx.fillRect(5, 4, 2, 3);
    ctx.fillRect(7, 3, 2, 4);
    ctx.fillRect(9, 5, 2, 3);
  }

  _drawBoard(ctx, p, ts) {
    ctx.fillStyle = p.wall;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#eee";
    ctx.fillRect(2, 3, ts - 4, ts - 6);
  }

  _drawChair(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    ctx.fillStyle = "#5c3317";
    ctx.fillRect(5, 8, 6, 6);
  }

  _drawStairs(ctx, p, ts) {
    ctx.fillStyle = p.floor;
    ctx.fillRect(0, 0, ts, ts);
    for (let i = 0; i < 3; i++) {
      const shade = this._darken(p.floor, 20 + i * 15);
      ctx.fillStyle = shade;
      ctx.fillRect(2, 4 + i * 4, ts - 4, 3);
    }
  }

  _drawCharSprites(ctx, palette, ts, cols, tileRows) {
    const oy = tileRows * ts;
    const directions = [Facing.DOWN, Facing.UP, Facing.LEFT, Facing.RIGHT];

    for (let frame = 0; frame < 2; frame++) {
      for (let dir = 0; dir < 4; dir++) {
        const cx = dir * ts;
        const cy = oy + frame * ts;
        ctx.fillStyle = palette.accent;
        ctx.fillRect(cx + 3, cy + 3, ts - 6, ts - 6);

        ctx.fillStyle = this._darken(palette.accent, 50);
        const mid = cx + ts / 2;
        const midy = cy + ts / 2;
        ctx.beginPath();
        switch (directions[dir]) {
          case Facing.DOWN:
            ctx.moveTo(mid - 2, midy + 1 + frame);
            ctx.lineTo(mid + 2, midy + 1 + frame);
            ctx.lineTo(mid, midy + 4 + frame);
            break;
          case Facing.UP:
            ctx.moveTo(mid - 2, midy - 1 - frame);
            ctx.lineTo(mid + 2, midy - 1 - frame);
            ctx.lineTo(mid, midy - 4 - frame);
            break;
          case Facing.LEFT:
            ctx.moveTo(mid - 1 - frame, midy - 2);
            ctx.lineTo(mid - 1 - frame, midy + 2);
            ctx.lineTo(mid - 4 - frame, midy);
            break;
          case Facing.RIGHT:
            ctx.moveTo(mid + 1 + frame, midy - 2);
            ctx.lineTo(mid + 1 + frame, midy + 2);
            ctx.lineTo(mid + 4 + frame, midy);
            break;
        }
        ctx.fill();
      }
    }
  }

  getTileCoords(tileId) {
    const col = tileId % TILE_COLS;
    const row = Math.floor(tileId / TILE_COLS);
    return { sx: col * this.tileSize, sy: row * this.tileSize };
  }

  getCanvas() {
    return this.canvas;
  }

  getCharSprite(facing, frame) {
    const tileRows = Math.ceil(this.tileCount / TILE_COLS);
    const sx = facing * this.tileSize;
    const sy = (tileRows + frame) * this.tileSize;
    return { sx, sy };
  }

  _darken(hex, amount) {
    const num = parseInt(hex.replace("#", ""), 16);
    const r = Math.max(0, ((num >> 16) & 0xff) - amount);
    const g = Math.max(0, ((num >> 8) & 0xff) - amount);
    const b = Math.max(0, (num & 0xff) - amount);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }
}
