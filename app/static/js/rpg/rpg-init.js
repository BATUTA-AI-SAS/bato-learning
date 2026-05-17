/**
 * rpg-init.js — Bootstrap module for the RPG game world.
 * Reads server-injected game state, wires up all subsystems, and starts the engine.
 */

import { RPGEngine } from "./rpg-engine.js";
import { DialogueSystem } from "./rpg-dialogue.js";
import { ROOMS, getRoomBySlug, getFirstRoom } from "./rpg-rooms.js";

const LS_ROOM = "blearn.rpg.room";
const LS_X = "blearn.rpg.x";
const LS_Y = "blearn.rpg.y";
const LS_FACING = "blearn.rpg.facing";

function pickStartingRoom(gameState) {
  const saved = localStorage.getItem(LS_ROOM);
  if (saved && gameState.rooms[saved]?.unlocked) return saved;

  // First unlocked room that is not 100% complete
  for (const [slug, info] of Object.entries(gameState.rooms)) {
    if (info.unlocked && info.percent < 100) return slug;
  }
  // Fallback: first room definition
  return getFirstRoom().slug;
}

function restorePosition(roomSlug) {
  const savedRoom = localStorage.getItem(LS_ROOM);
  if (savedRoom !== roomSlug) return null;

  const x = parseInt(localStorage.getItem(LS_X), 10);
  const y = parseInt(localStorage.getItem(LS_Y), 10);
  const facing = localStorage.getItem(LS_FACING) || "down";

  if (Number.isFinite(x) && Number.isFinite(y)) {
    return { x, y, facing };
  }
  return null;
}

function savePosition(engine) {
  const pos = engine.getPlayerPosition?.();
  if (!pos) return;
  localStorage.setItem(LS_X, String(pos.x));
  localStorage.setItem(LS_Y, String(pos.y));
  localStorage.setItem(LS_FACING, pos.facing || "down");
}

function init() {
  const gameState = window.__BL_GAME_STATE;
  if (!gameState) {
    console.error("[rpg-init] No game state found on window.__BL_GAME_STATE");
    return;
  }

  const canvas = document.getElementById("rpg-canvas");
  const dialogueEl = document.getElementById("rpg-dialogue");

  const dialogue = new DialogueSystem(dialogueEl);

  const startRoom = pickStartingRoom(gameState);
  let currentRoom = startRoom;

  const engine = new RPGEngine(canvas, gameState, ROOMS, dialogue);

  // Restore player position if returning to the same room
  const saved = restorePosition(startRoom);
  if (saved) {
    engine.setPlayerPosition(saved.x, saved.y, saved.facing);
  }

  // Load starting room and start loop
  engine.loadRoom(startRoom);
  engine.start();

  // Update HUD
  const hudRoom = document.querySelector(".hud-room");
  const hudXp = document.querySelector(".hud-xp");
  if (hudRoom) hudRoom.textContent = getRoomBySlug(startRoom)?.name || startRoom;
  if (hudXp) hudXp.textContent = `XP: ${gameState.total_xp}`;

  // --- Event handlers ---

  engine.onPuzzleTrigger(({ phaseSlug, levelSlug }) => {
    savePosition(engine);
    localStorage.setItem(LS_ROOM, currentRoom);
    window.location.href = `/game/${phaseSlug}/${levelSlug}?from=world`;
  });

  engine.onRoomChange((targetSlug) => {
    currentRoom = targetSlug;
    localStorage.setItem(LS_ROOM, targetSlug);
    localStorage.removeItem(LS_X);
    localStorage.removeItem(LS_Y);
    localStorage.removeItem(LS_FACING);
    engine.loadRoom(targetSlug);

    if (hudRoom) hudRoom.textContent = getRoomBySlug(targetSlug)?.name || targetSlug;
  });

  engine.onNPCChat(() => {
    dialogue.show(
      "Don Ramón",
      "Don Ramón te mira esperando tu pregunta... [Usa el panel de chat en tu siguiente misión]"
    );
  });

  window.addEventListener("resize", () => {
    renderer.resize();
  });
}

// Run when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
