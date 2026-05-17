import { Tileset, Facing } from "./rpg-tileset.js";
import { InputManager } from "./rpg-input.js";
import { Renderer } from "./rpg-renderer.js";

const State = { IDLE: 0, MOVING: 1, DIALOGUE: 2, TRANSITION: 3 };
const MOVE_DURATION = 120;
const FACING_DX = [0, 0, -1, 1];
const FACING_DY = [1, -1, 0, 0];

const FACING_MAP = { down: Facing.DOWN, up: Facing.UP, left: Facing.LEFT, right: Facing.RIGHT };

function resolveFacing(val) {
  if (typeof val === "number") return val;
  return FACING_MAP[val] ?? Facing.DOWN;
}

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

    this.rooms = rooms;
    this.currentRoom = null;
    this.currentRoomSlug = null;
    this.collisionMap = null;

    // Build a flat Set of all completed level slugs from gameState
    this.completedSlugs = new Set();
    this.totalXp = 0;
    if (gameState) {
      this.totalXp = gameState.total_xp || 0;
      for (const roomInfo of Object.values(gameState.rooms || {})) {
        for (const slug of (roomInfo.levels_passed || [])) {
          this.completedSlugs.add(slug);
        }
      }
    }
    this.gameState = gameState;

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
    this.currentRoomSlug = roomSlug;
    const palette = room.palette || { floor: "#3a3a5c", wall: "#1a1a2e", accent: "#e07020" };
    this.renderer.setRoom(room.tiles, palette);
    this._buildCollisionMap(room);

    if (room.spawn) {
      this.player.x = room.spawn.x;
      this.player.y = room.spawn.y;
      this.player.facing = resolveFacing(room.spawn.facing);
    }

    this._state = State.IDLE;
  }

  getPlayerPosition() {
    return { x: this.player.x, y: this.player.y, facing: this.player.facing };
  }

  setPlayerPosition(x, y, facing) {
    this.player.x = x;
    this.player.y = y;
    if (facing !== undefined) this.player.facing = resolveFacing(facing);
  }

  onPuzzleTrigger(callback) { this._onPuzzleTrigger = callback; }
  onRoomChange(callback) { this._onRoomChange = callback; }
  onNPCChat(callback) { this._onNPCChat = callback; }

  // --- Game loop ---

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
    let px = this.player.x, py = this.player.y;
    if (this._state === State.MOVING) {
      const t = Math.min(1, (performance.now() - this._moveStart) / MOVE_DURATION);
      px = this._moveFrom.x + (this._moveTo.x - this._moveFrom.x) * t;
      py = this._moveFrom.y + (this._moveTo.y - this._moveFrom.y) * t;
    }

    const room = this.currentRoom;
    const objStates = (room?.objects || []).map(obj => {
      const nextLevel = this._nextLevelForObject(obj);
      return {
        x: obj.x, y: obj.y,
        hasPuzzle: obj.type === "puzzle_cluster" || obj.type === "boss",
        completed: nextLevel === null && (obj.levels?.length > 0),
        locked: obj.type === "door" && !this._isDoorUnlocked(obj),
      };
    });

    this.renderer.drawFrame({
      playerPos: { x: px, y: py },
      facing: this.player.facing,
      animFrame: this.animFrame,
      objects: objStates,
      completedSlugs: this.completedSlugs,
      hudData: { roomName: room?.name || "", xp: this.totalXp },
    });
  }

  // --- Input handlers ---

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
      if (this.dialogue) this.dialogue.advance();
      return;
    }
    if (this._state !== State.IDLE) return;

    const tx = this.player.x + FACING_DX[this.player.facing];
    const ty = this.player.y + FACING_DY[this.player.facing];
    const obj = this._findObjectAt(tx, ty);
    if (!obj) return;

    if (obj.type === "puzzle_cluster" || obj.type === "boss") {
      this._triggerPuzzle(obj);
    } else if (obj.type === "npc") {
      this._triggerNPC(obj);
    } else if (obj.type === "door") {
      this._triggerDoor(obj);
    }
  }

  _handleCancel() {
    if (this._state === State.DIALOGUE && this.dialogue) {
      this.dialogue.skip();
    }
  }

  // --- Interaction logic ---

  _triggerPuzzle(obj) {
    const nextLevel = this._nextLevelForObject(obj);
    if (!nextLevel) {
      this._showDialogue("NARRADOR", ["Ya completaste todos los desafíos de esta estación."], () => {});
      return;
    }

    const lines = obj.intro_dialogue?.lines || [`Desafío: ${obj.label || nextLevel}`];
    this._showDialogue(
      obj.intro_dialogue?.speaker || "NARRADOR",
      lines,
      () => {
        this._state = State.TRANSITION;
        this.renderer.fadeToBlack(300).then(() => {
          this._state = State.IDLE;
          if (this._onPuzzleTrigger) {
            this._onPuzzleTrigger({
              phaseSlug: this.currentRoomSlug,
              levelSlug: nextLevel,
            });
          }
        });
      }
    );
  }

  _triggerNPC(obj) {
    const progress = this._roomProgressPercent();
    let dialogueData;
    if (obj.dialogues) {
      if (progress >= 100 && obj.dialogues.progress_100) dialogueData = obj.dialogues.progress_100;
      else if (progress >= 50 && obj.dialogues.progress_50) dialogueData = obj.dialogues.progress_50;
      else dialogueData = obj.dialogues.progress_0;
    }
    const lines = dialogueData?.lines || ["..."];
    const speaker = dialogueData?.speaker || obj.label || "NPC";

    this._showDialogue(speaker, lines, () => {
      if (this._onNPCChat) this._onNPCChat();
    });
  }

  _triggerDoor(obj) {
    if (!this._isDoorUnlocked(obj)) {
      const lines = obj.locked_dialogue?.lines || ["La puerta está cerrada. Necesitas completar más tareas."];
      const speaker = obj.locked_dialogue?.speaker || "NARRADOR";
      this._showDialogue(speaker, lines, () => {});
      return;
    }

    const lines = obj.unlocked_dialogue?.lines || ["La puerta se abre."];
    const speaker = obj.unlocked_dialogue?.speaker || "NARRADOR";
    this._showDialogue(speaker, lines, () => {
      this._state = State.TRANSITION;
      this.renderer.fadeToBlack(300).then(() => {
        this._state = State.IDLE;
        if (this._onRoomChange) this._onRoomChange(obj.target_room);
      });
    });
  }

  _showDialogue(speaker, lines, onDone) {
    if (!this.dialogue) { onDone(); return; }
    this._state = State.DIALOGUE;
    // Don't disable input — _handleInteract checks state and delegates to dialogue.advance()
    this.dialogue.onComplete(() => {
      if (this._state === State.DIALOGUE) this._state = State.IDLE;
      onDone();
    });
    this.dialogue.show(lines, speaker);
  }

  // --- Helpers ---

  _nextLevelForObject(obj) {
    if (!obj.levels || obj.levels.length === 0) return null;
    for (const slug of obj.levels) {
      if (!this.completedSlugs.has(slug)) return slug;
    }
    return null;
  }

  _isDoorUnlocked(obj) {
    const pct = obj.requires_percent || 70;
    return this._roomProgressPercent() >= pct;
  }

  _roomProgressPercent() {
    const roomState = this.gameState?.rooms?.[this.currentRoomSlug];
    return roomState?.percent || 0;
  }

  _findObjectAt(x, y) {
    const objects = this.currentRoom?.objects;
    if (!objects) return null;
    return objects.find(o => o.x === x && o.y === y) || null;
  }

  _buildCollisionMap(room) {
    const SOLID_TILES = new Set([1, 3, 4, 5, 6, 7, 8, 12, 13]);
    this.collisionMap = [];
    for (let y = 0; y < 15; y++) {
      const row = [];
      for (let x = 0; x < 20; x++) {
        const tileId = room.tiles[y]?.[x] ?? 0;
        row.push(SOLID_TILES.has(tileId));
      }
      this.collisionMap.push(row);
    }
    // NPC tiles are walkable-adjacent but not walkable-on
    if (room.objects) {
      for (const obj of room.objects) {
        if (obj.type === "npc") {
          this.collisionMap[obj.y][obj.x] = true;
        }
      }
    }
  }
}

export { Tileset, InputManager, Renderer, Facing, State };
