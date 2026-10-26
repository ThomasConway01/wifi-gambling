/**
 * Web Audio API Procedural Sound Engine
 * Zero dependencies, works offline, completely self-contained.
 */

class CasinoAudioEngine {
    constructor() {
        this.ctx = null;
        this.muted = false;
        this.masterVolume = 0.75;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioCtx();
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        return this.muted;
    }

    /** Clay chip placement sound */
    playChipSound() {
        if (this.muted) return;
        this.init();

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1600 + Math.random() * 400, now);
        osc.frequency.exponentialRampToValueAtTime(350, now + 0.04);

        gain.gain.setValueAtTime(0.4 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.05);
    }

    /** Ball bouncing against roulette pocket fret */
    playBallBounce() {
        if (this.muted) return;
        this.init();

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        const baseFreq = 2400 + Math.random() * 600;
        osc.frequency.setValueAtTime(baseFreq, now);
        osc.frequency.exponentialRampToValueAtTime(700, now + 0.025);

        gain.gain.setValueAtTime(0.3 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.03);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.03);
    }

    /** Dramatic heartbeat for high stakes / ALL IN bets */
    playHeartbeat() {
        if (this.muted) return;
        this.init();

        const now = this.ctx.currentTime;
        const playBeat = (time, freq, dur) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, time);
            osc.frequency.exponentialRampToValueAtTime(25, time + dur);

            gain.gain.setValueAtTime(0.6 * this.masterVolume, time);
            gain.gain.exponentialRampToValueAtTime(0.001, time + dur);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(time);
            osc.stop(time + dur);
        };

        playBeat(now, 90, 0.12);
        playBeat(now + 0.18, 75, 0.20);
    }

    /** Winning fanfare / celebration */
    playWinFanfare() {
        if (this.muted) return;
        this.init();

        const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98]; // C5, E5, G5, C6, E6, G6
        notes.forEach((freq, idx) => {
            const now = this.ctx.currentTime + idx * 0.08;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now);

            gain.gain.setValueAtTime(0.35 * this.masterVolume, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.4);
        });
    }

    /** Dramatic bust / Wi-Fi disconnect buzzer */
    playBustSound() {
        if (this.muted) return;
        this.init();

        const now = this.ctx.currentTime;
        
        // Low saw buzz
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(160, now);
        osc.frequency.exponentialRampToValueAtTime(30, now + 0.9);

        gain.gain.setValueAtTime(0.6 * this.masterVolume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.95);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.95);

        // Power-down glitch pulse
        const osc2 = this.ctx.createOscillator();
        const gain2 = this.ctx.createGain();
        osc2.type = 'square';
        osc2.frequency.setValueAtTime(80, now + 0.1);
        osc2.frequency.exponentialRampToValueAtTime(20, now + 0.8);

        gain2.gain.setValueAtTime(0.3 * this.masterVolume, now + 0.1);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.85);

        osc2.connect(gain2);
        gain2.connect(this.ctx.destination);
        osc2.start(now + 0.1);
        osc2.stop(now + 0.85);
    }
}

window.casinoAudio = new CasinoAudioEngine();
