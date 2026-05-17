import { RPGEngine } from "./rpg-engine.js";
import { DialogueSystem } from "./rpg-dialogue.js";
import { ROOMS, getRoomBySlug, getFirstRoom, ROOM_ORDER } from "./rpg-rooms.js";

const LS_ROOM = "blearn.rpg.room";
const LS_X = "blearn.rpg.x";
const LS_Y = "blearn.rpg.y";
const LS_FACING = "blearn.rpg.facing";

function pickStartingRoom(gameState) {
  const saved = localStorage.getItem(LS_ROOM);
  if (saved && ROOMS[saved] && gameState.rooms[saved]?.unlocked) return saved;

  for (const slug of ROOM_ORDER) {
    const info = gameState.rooms[slug];
    if (info && info.unlocked && info.percent < 100) return slug;
  }
  return getFirstRoom().slug;
}

function restorePosition(roomSlug) {
  if (localStorage.getItem(LS_ROOM) !== roomSlug) return null;
  const x = parseInt(localStorage.getItem(LS_X), 10);
  const y = parseInt(localStorage.getItem(LS_Y), 10);
  const facing = localStorage.getItem(LS_FACING) || "down";
  if (Number.isFinite(x) && Number.isFinite(y)) return { x, y, facing };
  return null;
}

function savePosition(engine, roomSlug) {
  const pos = engine.getPlayerPosition();
  if (!pos) return;
  localStorage.setItem(LS_ROOM, roomSlug);
  localStorage.setItem(LS_X, String(pos.x));
  localStorage.setItem(LS_Y, String(pos.y));
  localStorage.setItem(LS_FACING, String(pos.facing));
}

function init() {
  const gameState = window.__BL_GAME_STATE;
  if (!gameState) {
    console.error("[rpg] No game state");
    return;
  }

  const canvas = document.getElementById("rpg-canvas");
  const dialogueEl = document.getElementById("rpg-dialogue");
  if (!canvas || !dialogueEl) {
    console.error("[rpg] Missing DOM elements");
    return;
  }

  const dialogue = new DialogueSystem(dialogueEl);
  const engine = new RPGEngine(canvas, gameState, ROOMS, dialogue);
  window.__RPG_ENGINE = engine;

  let currentRoom = pickStartingRoom(gameState);

  const saved = restorePosition(currentRoom);
  if (saved) engine.setPlayerPosition(saved.x, saved.y, saved.facing);

  engine.loadRoom(currentRoom);
  engine.start();

  // HUD
  const hudRoom = document.querySelector(".hud-room");
  const hudXp = document.querySelector(".hud-xp");
  function updateHud(slug) {
    if (hudRoom) hudRoom.textContent = (getRoomBySlug(slug)?.name || slug).toUpperCase();
    if (hudXp) hudXp.textContent = `XP: ${gameState.total_xp || 0}`;
  }
  updateHud(currentRoom);

  // Events
  engine.onPuzzleTrigger(({ phaseSlug, levelSlug }) => {
    savePosition(engine, currentRoom);
    window.location.href = `/game/${phaseSlug}/${levelSlug}?from=world`;
  });

  engine.onRoomChange((targetSlug) => {
    currentRoom = targetSlug;
    localStorage.setItem(LS_ROOM, targetSlug);
    localStorage.removeItem(LS_X);
    localStorage.removeItem(LS_Y);
    engine.loadRoom(targetSlug);
    updateHud(targetSlug);
  });

  engine.onNPCChat(() => {
    // MVP: NPC chat is handled via dialogue system in the engine
  });

  window.addEventListener("resize", () => engine.renderer.resize());
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
