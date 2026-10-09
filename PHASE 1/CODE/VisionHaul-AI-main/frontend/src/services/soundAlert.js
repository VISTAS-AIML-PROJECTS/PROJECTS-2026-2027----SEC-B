/**
 * Web Audio API Sound Synthesizer for Heavy Vehicle Surveillance Alerts.
 * Zero external audio assets required.
 */
class SoundAlertService {
  constructor() {
    this.audioCtx = null;
    this.isMuted = false;
    this.volume = 0.6;
    this.activeOscillator = null;
  }

  _initContext() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (muted && this.activeOscillator) {
      this.stop();
    }
  }

  setVolume(vol) {
    this.volume = Math.max(0, Math.min(1, vol));
  }

  playSiren(durationSec = 2.5) {
    if (this.isMuted) return;
    try {
      this._initContext();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sawtooth';
      
      // Siren frequency modulation (900Hz <-> 1400Hz alternating alarm sweep)
      osc.frequency.setValueAtTime(880, now);
      for (let t = 0; t < durationSec; t += 0.4) {
        osc.frequency.linearRampToValueAtTime(1400, now + t + 0.2);
        osc.frequency.linearRampToValueAtTime(880, now + t + 0.4);
      }

      // Gain envelope
      gain.gain.setValueAtTime(this.volume * 0.4, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + durationSec);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(now);
      osc.stop(now + durationSec);
      this.activeOscillator = osc;
    } catch (e) {
      console.warn('Audio synthesis note:', e);
    }
  }

  playWarningBeep() {
    if (this.isMuted) return;
    try {
      this._initContext();
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(650, now);
      osc.frequency.setValueAtTime(800, now + 0.12);

      gain.gain.setValueAtTime(this.volume * 0.35, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(now);
      osc.stop(now + 0.35);
    } catch (e) {
      console.warn('Audio warning note:', e);
    }
  }

  stop() {
    if (this.activeOscillator) {
      try {
        this.activeOscillator.stop();
      } catch (e) {}
      this.activeOscillator = null;
    }
  }
}

export const soundAlert = new SoundAlertService();
