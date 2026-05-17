/**
 * rpg-dialogue.js — Zelda-style dialogue box system.
 * Typewriter text effect, speaker name, line queue.
 */

const CHAR_DELAY_MS = 30;

export class DialogueSystem {
  /** @param {HTMLElement} overlayEl - the #rpg-dialogue DOM element */
  constructor(overlayEl) {
    this._overlay = overlayEl;
    this._speakerEl = overlayEl.querySelector('.dialogue-speaker');
    this._textEl = overlayEl.querySelector('.dialogue-text');
    this._hintEl = overlayEl.querySelector('.dialogue-advance-hint');

    this._queue = [];
    this._currentLine = '';
    this._charIndex = 0;
    this._timer = null;
    this._active = false;
    this._typing = false;
    this._isNarrador = false;
    this._onCompleteCb = null;
  }

  /**
   * Queue lines, show overlay, start typewriter on first line.
   * @param {string[]} lines
   * @param {string} speakerName
   */
  show(lines, speakerName) {
    if (!lines || lines.length === 0) return;

    this._queue = [...lines];
    this._isNarrador = speakerName === 'NARRADOR';
    this._active = true;

    // Speaker display
    if (this._isNarrador) {
      this._speakerEl.textContent = '';
      this._speakerEl.style.display = 'none';
      this._textEl.classList.add('narrador');
    } else {
      this._speakerEl.textContent = speakerName;
      this._speakerEl.style.display = '';
      this._textEl.classList.remove('narrador');
    }

    this._overlay.classList.remove('hidden');
    this._startLine(this._queue.shift());
  }

  /** If mid-typewrite: instant-complete. If complete: next line or close. */
  advance() {
    if (!this._active) return;

    if (this._typing) {
      // Instant-complete current line
      this._stopTimer();
      this._textEl.textContent = this._currentLine;
      this._typing = false;
      this._textEl.classList.remove('typing');
      this._showHint();
    } else if (this._queue.length > 0) {
      this._hideHint();
      this._startLine(this._queue.shift());
    } else {
      this._close();
    }
  }

  /** @returns {boolean} */
  isActive() {
    return this._active;
  }

  /** Fires when ALL lines dismissed and overlay hidden. */
  onComplete(callback) {
    this._onCompleteCb = callback;
  }

  /** Force-complete all lines, close immediately. */
  skip() {
    this._stopTimer();
    this._queue = [];
    this._close();
  }

  /** Cleanup timers and references. */
  destroy() {
    this._stopTimer();
    this._queue = [];
    this._active = false;
    this._onCompleteCb = null;
  }

  // -- Private ---------------------------------------------------------------

  /** @param {string} line */
  _startLine(line) {
    this._currentLine = line;
    this._charIndex = 0;
    this._typing = true;
    this._textEl.textContent = '';
    this._textEl.classList.add('typing');
    this._hideHint();
    this._tick();
  }

  _tick() {
    this._timer = setTimeout(() => {
      this._charIndex++;
      this._textEl.textContent = this._currentLine.slice(0, this._charIndex);

      if (this._charIndex >= this._currentLine.length) {
        this._typing = false;
        this._textEl.classList.remove('typing');
        this._showHint();
      } else {
        this._tick();
      }
    }, CHAR_DELAY_MS);
  }

  _stopTimer() {
    if (this._timer !== null) {
      clearTimeout(this._timer);
      this._timer = null;
    }
  }

  _showHint() {
    this._hintEl.classList.add('visible');
  }

  _hideHint() {
    this._hintEl.classList.remove('visible');
  }

  _close() {
    this._active = false;
    this._typing = false;
    this._textEl.classList.remove('typing');
    this._overlay.classList.add('hidden');
    this._hideHint();
    if (this._onCompleteCb) this._onCompleteCb();
  }
}
