import { Tileset, Facing } from "./rpg-tileset.js";
import { InputManager } from "./rpg-input.js";
import { Renderer } from "./rpg-renderer.js";

const State = { IDLE: 0, MOVING: 1, DIALOGUE: 2, TRANSITION: 3 };
const MOVE_DURATION = 120;
const FACING_DX = [0, 0, -1, 1];
const FACING_DY = [1, -1, 0, 0];

function facingFromDelta(dx, dy) {
  if (dy > 0) return Facing.DOWN;
  if (dy < 0) return Facing.UP;
  if (dx < 0) return Facing.LEFT;
  return Facing.RIGHT;
}

export class RPGEngine {
  constructor(canvas, gameState, rooms, dialogueSystem) {
    this.tileset = new Tileset(16);
    this.renderer = new Renderer(canvas, this.tileset);
    this.input = new InputManager();
    this.dialogue = dialogueSystem || null;

    this.gameState = gameState;
    this.rooms = rooms;
    this.currentRoom = null;
    this.collisionMap = null;

    this.player = { x: 0, y: 0, facing: Facing.DOWN };
    this.animFrame = 0;
    this._animFrameTimer = 0;

    this._state = State.IDLE;
    this._moveStart = null;
    this._moveFrom = null;
    this._moveTo = null;
    this._running = false;
    this._rafId = null;
    this._lastTime = 0;

    this._onPuzzleTrigger = null;
    this._onRoomChange = null;
    this._onNPCChat = null;

    this.input.onMove((dx, dy) => this._handleMove(dx, dy));
    this.input.onInteract(() => this._handleInteract());
    this.input.onCancel(() => this._handleCancel());
  }

  start() {
    if (this._running) return;
    this._running = true;
    this._lastTime = performance.now();
    this._tick();
  }

  stop() {
    this._running = false;
    if (this._rafId) {
      cancelAnimationFrame(this._rafId);
      this._rafId = null;
    }
  }

  loadRoom(roomSlug) {
    const room = this.rooms[roomSlug];
    if (!room) return;

    this.currentRoom = room;
    const palette = room.palette || { floor: "#3a3a5c", wall: "#1a1a2e", accent: "#e07020" };
    this.renderer.setRoom(room.tiles, palette);
    this._buildCollisionMap(room);

    if (room.spawn) {
      this.player.x = room.spawn.x;
      this.player.y = room.spawn.y;
      this.player.facing = room.spawn.facing ?? Facing.DOWN;
    }

    this._state = State.IDLE;
  }

  getPlayerPosition() {
    return { x: this.player.x, y: this.player.y, facing: this.player.facing };
  }

  setPlayerPosition(x, y, facing) {
    this.player.x = x;
    this.player.y = y;
    this.player.facing = facing ?? this.player.facing;
  }

  onPuzzleTrigger(callback) { this._onPuzzleTrigger = callback; }
  onRoomChange(callback) { this._onRoomChange = callback; }
  onNPCChat(callback) { this._onNPCChat = callback; }

  _tick() {
    if (!this._running) return;
    const now = performance.now();
    const dt = now - this._lastTime;
    this._lastTime = now;

    this._update(dt, now);
    this._render();

    this._rafId = requestAnimationFrame(() => this._tick());
  }

  _update(dt, now) {
    this._animFrameTimer += dt;
    if (this._animFrameTimer > 300) {
      this._animFrameTimer = 0;
      this.animFrame = (this.animFrame + 1) % 2;
    }

    if (this._state === State.MOVING) {
      const elapsed = now - this._moveStart;
      if (elapsed >= MOVE_DURATION) {
        this.player.x = this._moveTo.x;
        this.player.y = this._moveTo.y;
        this._state = State.IDLE;
      }
    }
  }

  _render() {
    let playerPos = { x: this.player.x, y: this.player.y };

    if (this._state === State.MOVING) {
      const elapsed = performance.now() - this._moveStart;
      const t = Math.min(1, elapsed / MOVE_DURATION);
      playerPos = {
        x: this._moveFrom.x + (this._moveTo.x - this._moveFrom.x) * t,
        y: this._moveFrom.y + (this._moveTo.y - this._moveFrom.y) * t,
      };
    }

    const room = this.currentRoom;
    this.renderer.drawFrame({
      playerPos,
      facing: this.player.facing,
      animFrame: this.animFrame,
      objects: room?.objects || [],
      completedSlugs: this.gameState?.completedSlugs || new Set(),
      npc: room?.npc || null,
      hudData: {
        roomName: room?.name || "",
        xp: this.gameState?.xp ?? 0,
      },
    });
  }

  _handleMove(dx, dy) {
    if (this._state !== State.IDLE) return;

    this.player.facing = facingFromDelta(dx, dy);
    const nx = this.player.x + dx;
    const ny = this.player.y + dy;

    if (nx < 0 || nx >= 20 || ny < 0 || ny >= 15) return;
    if (this.collisionMap && this.collisionMap[ny][nx]) return;

    this._state = State.MOVING;
    this._moveStart = performance.now();
    this._moveFrom = { x: this.player.x, y: this.player.y };
    this._moveTo = { x: nx, y: ny };
  }

  _handleInteract() {
    if (this._state === State.DIALOGUE) {
      if (this.dialogue && this.dialogue.advance) {
        this.dialogue.advance();
      }
      return;
    }

    if (this._state !== State.IDLE) return;

    const tx = this.player.x + FACING_DX[this.player.facing];
    const ty = this.player.y + FACING_DY[this.player.facing];
    const room = this.currentRoom;
    if (!room) return;

    const obj = this._findObjectAt(tx, ty);
    if (!obj) return;

    if (obj.type === "puzzle_cluster") {
      this._triggerPuzzle(obj);
    } else if (obj.type === "npc") {
      this._triggerNPC(obj);
    } else if (obj.type === "door") {
      this._triggerDoor(obj);
    }
  }

  _handleCancel() {
    if (this._state === State.DIALOGUE && this.dialogue && this.dialogue.skip) {
      this.dialogue.skip();
    }
  }

  _triggerPuzzle(obj) {
    this._state = State.DIALOGUE;
    this.input.disable();

    const finish = () => {
      this._state = State.TRANSITION;
      this.renderer.flashWhite(200).then(() => {
        this.input.enable();
        this._state = State.IDLE;
        if (this._onPuzzleTrigger) {
          this._onPuzzleTrigger({ phaseSlug: obj.phaseSlug, levelSlug: obj.levelSlug });
        }
      });
    };

    if (this.dialogue && obj.introLines) {
      this.dialogue.show(obj.introLines, () => finish());
    } else {
      finish();
    }
  }

  _triggerNPC(obj) {
    this._state = State.DIALOGUE;
    this.input.disable();

    const finish = () => {
      this.input.enable();
      this._state = State.IDLE;
      if (this._onNPCChat) this._onNPCChat();
    };

    if (this.dialogue && obj.lines) {
      this.dialogue.show(obj.lines, () => finish());
    } else {
      finish();
    }
  }

  _triggerDoor(obj) {
    if (obj.locked) {
      this._state = State.DIALOGUE;
      this.input.disable();
      const msg = obj.lockedMessage || ["Locked."];
      if (this.dialogue) {
        this.dialogue.show(msg, () => {
          this.input.enable();
          this._state = State.IDLE;
        });
      } else {
        this.input.enable();
        this._state = State.IDLE;
      }
      return;
    }

    this._state = State.TRANSITION;
    this.input.disable();
    this.renderer.fadeToBlack(300).then(() => {
      this.input.enable();
      this._state = State.IDLE;
      if (this._onRoomChange) this._onRoomChange(obj.targetRoom);
    });
  }

  _findObjectAt(x, y) {
    const objects = this.currentRoom?.objects;
    if (!objects) return null;
    return objects.find(o => o.x === x && o.y === y) || null;
  }

  _buildCollisionMap(room) {
    const WALL_TILES = new Set([1, 3, 4, 5, 6, 7, 8, 13]);
    this.collisionMap = [];

    for (let y = 0; y < 15; y++) {
      const row = [];
      for (let x = 0; x < 20; x++) {
        const tileId = room.tiles[y]?.[x] ?? 0;
        row.push(WALL_TILES.has(tileId));
      }
      this.collisionMap.push(row);
    }

    if (room.objects) {
      for (const obj of room.objects) {
        if (obj.solid !== false && obj.type !== "door") {
          this.collisionMap[obj.y][obj.x] = true;
        }
      }
    }
  }
}

export { Tileset, InputManager, Renderer, Facing, State };
