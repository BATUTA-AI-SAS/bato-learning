const MOVE_KEYS = {
  KeyW: [0, -1], KeyA: [-1, 0], KeyS: [0, 1], KeyD: [1, 0],
  ArrowUp: [0, -1], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowRight: [1, 0],
};
const INTERACT_KEYS = new Set(["Enter", "KeyE", "Space"]);
const CANCEL_KEYS = new Set(["Escape"]);

const INITIAL_DELAY = 180;
const REPEAT_INTERVAL = 100;

export class InputManager {
  constructor() {
    this._moveCallback = null;
    this._interactCallback = null;
    this._cancelCallback = null;
    this._enabled = true;
    this._activeKey = null;
    this._repeatTimer = null;
    this._initialTimer = null;
    this._heldKeys = [];

    this._onKeyDown = this._onKeyDown.bind(this);
    this._onKeyUp = this._onKeyUp.bind(this);
    window.addEventListener("keydown", this._onKeyDown);
    window.addEventListener("keyup", this._onKeyUp);
  }

  onMove(callback) { this._moveCallback = callback; }
  onInteract(callback) { this._interactCallback = callback; }
  onCancel(callback) { this._cancelCallback = callback; }

  enable() { this._enabled = true; }

  disable() {
    this._enabled = false;
    this._stopRepeat();
    this._heldKeys = [];
    this._activeKey = null;
  }

  destroy() {
    window.removeEventListener("keydown", this._onKeyDown);
    window.removeEventListener("keyup", this._onKeyUp);
    this._stopRepeat();
  }

  _onKeyDown(e) {
    if (!this._enabled) return;
    const code = e.code;

    if (MOVE_KEYS[code]) {
      e.preventDefault();
      if (this._activeKey === code) return;
      this._heldKeys = this._heldKeys.filter(k => k !== code);
      this._heldKeys.push(code);
      this._activateKey(code);
      return;
    }

    if (INTERACT_KEYS.has(code)) {
      e.preventDefault();
      if (this._interactCallback) this._interactCallback();
      return;
    }

    if (CANCEL_KEYS.has(code)) {
      e.preventDefault();
      if (this._cancelCallback) this._cancelCallback();
    }
  }

  _onKeyUp(e) {
    const code = e.code;
    if (!MOVE_KEYS[code]) return;

    this._heldKeys = this._heldKeys.filter(k => k !== code);
    if (this._activeKey === code) {
      this._stopRepeat();
      this._activeKey = null;
      if (this._heldKeys.length > 0) {
        this._activateKey(this._heldKeys[this._heldKeys.length - 1]);
      }
    }
  }

  _activateKey(code) {
    this._stopRepeat();
    this._activeKey = code;
    this._fireMove(code);

    this._initialTimer = setTimeout(() => {
      this._repeatTimer = setInterval(() => {
        this._fireMove(code);
      }, REPEAT_INTERVAL);
    }, INITIAL_DELAY);
  }

  _fireMove(code) {
    if (this._moveCallback) {
      const [dx, dy] = MOVE_KEYS[code];
      this._moveCallback(dx, dy);
    }
  }

  _stopRepeat() {
    if (this._initialTimer) { clearTimeout(this._initialTimer); this._initialTimer = null; }
    if (this._repeatTimer) { clearInterval(this._repeatTimer); this._repeatTimer = null; }
  }
}
