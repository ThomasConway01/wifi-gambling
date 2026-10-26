/**
 * Luxury 3D Canvas European Roulette Wheel
 * Physics-based deceleration, dynamic lighting, ball bounce spark particles, and winning pocket aura.
 */

class RouletteWheel {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // European roulette sequence (clockwise)
        this.numbers = [
            0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5,
            24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
        ];
        this.redNumbers = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
        this.pocketCount = this.numbers.length;
        this.pocketAngle = (Math.PI * 2) / this.pocketCount;

        // Angles & State
        this.wheelAngle = 0;
        this.ballAngle = -Math.PI / 2;
        this.ballRadius = 0;
        this.isSpinning = false;
        this.isIdle = true;
        this.winningPocketIndex = -1;
        this.winningPocketGlow = 0; // 0 to 1
        this.particles = [];

        this.setupDPI();
        window.addEventListener('resize', () => this.setupDPI());

        this.lastTime = performance.now();
        requestAnimationFrame((t) => this.renderLoop(t));
    }

    setupDPI() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const size = Math.min(rect.width || 440, 480);
        this.width = size;
        this.height = size;
        this.canvas.width = size * dpr;
        this.canvas.height = size * dpr;
        this.ctx.scale(dpr, dpr);
        this.radius = size / 2;
    }

    getNumberColor(num) {
        if (num === 0) return '#059669'; // Emerald Green
        return this.redNumbers.has(num) ? '#e11d48' : '#111827'; // Crimson Red or Obsidian Black
    }

    spawnSparks(x, y) {
        for (let i = 0; i < 6; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 60,
                vy: (Math.random() - 0.5) * 60,
                life: 1.0,
                color: Math.random() > 0.5 ? '#fef08a' : '#fbbf24',
                size: 2 + Math.random() * 2
            });
        }
    }

    draw() {
        const ctx = this.ctx;
        const cx = this.width / 2;
        const cy = this.height / 2;
        const r = this.radius;

        ctx.clearRect(0, 0, this.width, this.height);

        // 1. Luxury Outer Mahogany Bezel with Metallic Studs
        const outerWoodGrad = ctx.createRadialGradient(cx, cy, r * 0.75, cx, cy, r);
        outerWoodGrad.addColorStop(0, '#1c1917');
        outerWoodGrad.addColorStop(0.5, '#451a03');
        outerWoodGrad.addColorStop(0.8, '#78350f');
        outerWoodGrad.addColorStop(0.96, '#291002');
        outerWoodGrad.addColorStop(1, '#0c0a09');

        ctx.beginPath();
        ctx.arc(cx, cy, r - 5, 0, Math.PI * 2);
        ctx.fillStyle = outerWoodGrad;
        ctx.fill();

        // Gold Rim Rings
        ctx.lineWidth = 3.5;
        ctx.strokeStyle = '#d97706';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, r - 2, 0, Math.PI * 2);
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = '#fef08a';
        ctx.stroke();

        // 16 Brass Rivets/Studs around bezel
        for (let st = 0; st < 16; st++) {
            const stAngle = (st * Math.PI * 2) / 16;
            const sx = cx + Math.cos(stAngle) * (r - 10);
            const sy = cy + Math.sin(stAngle) * (r - 10);

            ctx.beginPath();
            ctx.arc(sx, sy, 2.5, 0, Math.PI * 2);
            ctx.fillStyle = '#fbbf24';
            ctx.fill();
            ctx.strokeStyle = '#78350f';
            ctx.lineWidth = 0.8;
            ctx.stroke();
        }

        // 2. Brass Ball Track Ring
        const trackR = r * 0.88;
        ctx.beginPath();
        ctx.arc(cx, cy, trackR, 0, Math.PI * 2);
        ctx.strokeStyle = '#92400e';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Inner Brass Reflector Ring
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.84, 0, Math.PI * 2);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // 3. Wheel Rotor (Rotates by wheelAngle)
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(this.wheelAngle);

        const outerPocketsR = r * 0.84;
        const innerPocketsR = r * 0.54;

        // Draw each numbered pocket
        for (let i = 0; i < this.pocketCount; i++) {
            const num = this.numbers[i];
            const startAngle = i * this.pocketAngle - this.pocketAngle / 2;
            const endAngle = startAngle + this.pocketAngle;

            // Pocket Slice
            ctx.beginPath();
            ctx.arc(0, 0, outerPocketsR, startAngle, endAngle);
            ctx.arc(0, 0, innerPocketsR, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = this.getNumberColor(num);
            ctx.fill();

            // Winning Pocket Glow Aura
            if (i === this.winningPocketIndex && this.winningPocketGlow > 0) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(0, 0, outerPocketsR, startAngle, endAngle);
                ctx.arc(0, 0, innerPocketsR, endAngle, startAngle, true);
                ctx.closePath();
                ctx.fillStyle = `rgba(251, 191, 36, ${0.45 * this.winningPocketGlow})`;
                ctx.fill();
                ctx.restore();
            }

            // Polished Brass Fret Dividers
            ctx.beginPath();
            ctx.moveTo(Math.cos(startAngle) * innerPocketsR, Math.sin(startAngle) * innerPocketsR);
            ctx.lineTo(Math.cos(startAngle) * outerPocketsR, Math.sin(startAngle) * outerPocketsR);
            ctx.strokeStyle = '#fbbf24';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // White / Gold Number Text
            ctx.save();
            const textAngle = i * this.pocketAngle;
            ctx.rotate(textAngle);
            ctx.translate((outerPocketsR + innerPocketsR) / 2, 0);
            ctx.rotate(Math.PI / 2); // Rotate text radially
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px "JetBrains Mono", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor = 'rgba(0,0,0,0.8)';
            ctx.shadowBlur = 3;
            ctx.fillText(num.toString(), 0, 0);
            ctx.restore();
        }

        // 4. Center Brass Cone & Turret
        const innerGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, innerPocketsR);
        innerGrad.addColorStop(0, '#fef08a');
        innerGrad.addColorStop(0.3, '#fbbf24');
        innerGrad.addColorStop(0.7, '#b45309');
        innerGrad.addColorStop(1, '#451a03');

        ctx.beginPath();
        ctx.arc(0, 0, innerPocketsR, 0, Math.PI * 2);
        ctx.fillStyle = innerGrad;
        ctx.fill();
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // 8 Brass Turret Spokes
        for (let s = 0; s < 8; s++) {
            const sAngle = (s * Math.PI) / 4;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(Math.cos(sAngle) * (innerPocketsR * 0.72), Math.sin(sAngle) * (innerPocketsR * 0.72));
            ctx.lineWidth = 3.5;
            ctx.strokeStyle = '#fef08a';
            ctx.stroke();
        }

        // Center Gold Crown Cap
        const capGrad = ctx.createRadialGradient(-3, -3, 1, 0, 0, innerPocketsR * 0.28);
        capGrad.addColorStop(0, '#ffffff');
        capGrad.addColorStop(0.4, '#fbbf24');
        capGrad.addColorStop(0.9, '#92400e');
        capGrad.addColorStop(1, '#451a03');

        ctx.beginPath();
        ctx.arc(0, 0, innerPocketsR * 0.28, 0, Math.PI * 2);
        ctx.fillStyle = capGrad;
        ctx.fill();
        ctx.strokeStyle = '#fef08a';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.restore(); // Restore wheel rotation

        // 5. Draw Ivory Ball
        if (this.isSpinning || !this.isIdle) {
            const bx = cx + Math.cos(this.ballAngle) * this.ballRadius;
            const by = cy + Math.sin(this.ballAngle) * this.ballRadius;

            // Soft Ball Shadow
            ctx.beginPath();
            ctx.arc(bx + 3, by + 4, 7, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
            ctx.fill();

            // Ivory Ball Gradient
            const ballGrad = ctx.createRadialGradient(bx - 2.5, by - 2.5, 1, bx, by, 7.5);
            ballGrad.addColorStop(0, '#ffffff');
            ballGrad.addColorStop(0.6, '#f4f4f5');
            ballGrad.addColorStop(0.95, '#cbd5e1');
            ballGrad.addColorStop(1, '#94a3b8');

            ctx.beginPath();
            ctx.arc(bx, by, 7, 0, Math.PI * 2);
            ctx.fillStyle = ballGrad;
            ctx.fill();
            ctx.strokeStyle = '#64748b';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // 6. Draw Spark Particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    renderLoop(timestamp) {
        const dt = Math.min(0.05, (timestamp - this.lastTime) / 1000);
        this.lastTime = timestamp;

        if (this.isIdle && !this.isSpinning) {
            this.wheelAngle += 0.25 * dt;
        }

        // Update winning pocket pulse
        if (this.winningPocketGlow > 0) {
            this.winningPocketGlow = Math.max(0, this.winningPocketGlow - dt * 0.4);
        }

        // Update particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.life -= dt * 2.2;
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }

        this.draw();
        requestAnimationFrame((t) => this.renderLoop(t));
    }

    /**
     * Spin wheel to target number with physics deceleration and audio sync
     */
    spinTo(targetNumber, durationMs = 5200, onComplete = null) {
        if (this.isSpinning) return;
        this.isSpinning = true;
        this.isIdle = false;
        this.winningPocketIndex = -1;
        this.winningPocketGlow = 0;

        const targetIndex = this.numbers.indexOf(targetNumber);
        if (targetIndex === -1) {
            console.error("Invalid target number:", targetNumber);
            this.isSpinning = false;
            return;
        }

        // Indicator at top (-PI/2)
        const targetPocketCenterAngle = targetIndex * this.pocketAngle;

        const wheelRevs = 4 + Math.random() * 2;
        const startWheelAngle = this.wheelAngle % (Math.PI * 2);
        const finalWheelAngle = startWheelAngle + (wheelRevs * Math.PI * 2) - targetPocketCenterAngle - (Math.PI / 2);

        const ballRevs = 8 + Math.random() * 2;
        const startBallAngle = this.ballAngle % (Math.PI * 2);
        const finalBallAngle = startBallAngle - (ballRevs * Math.PI * 2);

        const startTime = performance.now();
        const outerTrackR = this.radius * 0.88;
        const pocketR = (this.radius * 0.84 + this.radius * 0.54) / 2;

        let lastBouncePocket = -1;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(1, elapsed / durationMs);

            const easeOut = 1 - Math.pow(1 - progress, 4);

            this.wheelAngle = startWheelAngle + (finalWheelAngle - startWheelAngle) * easeOut;

            if (progress < 0.65) {
                const ballProgress = progress / 0.65;
                const ballEase = 1 - Math.pow(1 - ballProgress, 2.5);
                this.ballAngle = startBallAngle + (finalBallAngle - startBallAngle) * ballEase;
                this.ballRadius = outerTrackR;
            } else {
                const dropProgress = (progress - 0.65) / 0.35;
                const dropEase = 1 - Math.pow(1 - dropProgress, 3);

                const remainingRevs = (1 - dropProgress) * 1.5;
                this.ballAngle = (finalWheelAngle + targetPocketCenterAngle) + remainingRevs;

                const bounce = Math.sin(dropProgress * Math.PI * 5) * (1 - dropProgress) * 7;
                this.ballRadius = pocketR + (outerTrackR - pocketR) * (1 - dropEase) + bounce;

                const currentRelIndex = Math.floor(Math.abs(remainingRevs * 5)) % this.pocketCount;
                if (currentRelIndex !== lastBouncePocket) {
                    lastBouncePocket = currentRelIndex;
                    if (window.casinoAudio) {
                        window.casinoAudio.playBallBounce();
                    }
                    // Spawn spark particles on bounce
                    const bx = this.width / 2 + Math.cos(this.ballAngle) * this.ballRadius;
                    const by = this.height / 2 + Math.sin(this.ballAngle) * this.ballRadius;
                    this.spawnSparks(bx, by);
                }
            }

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.ballAngle = -Math.PI / 2;
                this.ballRadius = pocketR;
                this.isSpinning = false;
                this.isIdle = true;
                this.winningPocketIndex = targetIndex;
                this.winningPocketGlow = 1.0;

                if (onComplete) {
                    onComplete(targetNumber);
                }
            }
        };

        requestAnimationFrame(animate);
    }
}

window.RouletteWheel = RouletteWheel;
