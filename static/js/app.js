/**
 * WiFi Time Roulette - Pure Green Felt Table Orchestrator
 * - Click wheel to spin
 * - Drag tokens onto table
 * - No buttons, pure tactile casino experience
 */

class RouletteApp {
    constructor() {
        this.selectedDevice = null;
        this.currentBets = [];
        this.totalWagerHours = 0;
        this.settings = {};

        this.initElements();
        this.initRouletteComponents();
        this.bindEvents();
        this.loadInitialData();

        // Refresh balance in background
        setInterval(() => this.fetchMyDevice(), 10000);
    }

    initElements() {
        this.hudDeviceBalance = document.getElementById('hudDeviceBalance');
        this.totalWagerEl = document.getElementById('totalWagerHours');
        this.wheelSpinTrigger = document.getElementById('wheelSpinTrigger');
        this.wheelSpinHint = document.getElementById('wheelSpinHint');
        this.recentNumbersList = document.getElementById('recentNumbersList');
    }

    initRouletteComponents() {
        this.wheel = new RouletteWheel('rouletteCanvas');
        this.table = new RouletteTable('rouletteTableContainer', (bets, totalHours) => {
            this.currentBets = bets;
            this.totalWagerHours = totalHours;
            this.updateWagerHUD();
        });
    }

    bindEvents() {
        // Clicking the wheel triggers the spin!
        this.wheelSpinTrigger?.addEventListener('click', () => {
            if (this.currentBets.length > 0 && !this.wheel.isSpinning) {
                this.executeSpin();
            } else if (this.currentBets.length === 0) {
                // Play chip tap sound to remind user to drag tokens
                if (window.casinoAudio) window.casinoAudio.playChipSound();
            }
        });

        // Outcome Modal Close
        document.getElementById('closeOutcomeModalBtn')?.addEventListener('click', () => {
            document.getElementById('outcomeModal')?.classList.add('hidden');
        });

        // Dismiss BUST Blackout
        document.getElementById('dismissBustBlackoutBtn')?.addEventListener('click', () => {
            document.getElementById('bustBlackoutModal')?.classList.add('hidden');
        });

        // Emergency Admin Pardon (Restore connection)
        document.getElementById('emergencyPardonBtn')?.addEventListener('click', async () => {
            if (this.selectedDevice) {
                await this.emergencyUnblock(this.selectedDevice.mac);
                document.getElementById('bustBlackoutModal')?.classList.add('hidden');
            }
        });
    }

    async loadInitialData() {
        await this.loadSettings();
        await this.fetchMyDevice();
        await this.fetchRecentNumbers();
    }

    async loadSettings() {
        try {
            const res = await fetch('/api/settings');
            this.settings = await res.json();
        } catch (e) {}
    }

    async fetchMyDevice() {
        try {
            const res = await fetch('/api/me');
            this.selectedDevice = await res.json();
            this.table.setDevice(this.selectedDevice);
            this.updateDeviceHUD();
        } catch (e) {
            console.error('Failed to fetch device', e);
        }
    }

    updateDeviceHUD() {
        if (!this.selectedDevice) return;
        const d = this.selectedDevice;
        const isBusted = d.status === 'LOCKED_OUT';

        if (this.hudDeviceBalance) {
            this.hudDeviceBalance.innerText = d.remaining_formatted;
            this.hudDeviceBalance.className = isBusted ? 'text-rose-500 font-bold line-through text-xl' : 'text-amber-300 font-extrabold text-xl';
        }
        this.updateWagerHUD();
    }

    updateWagerHUD() {
        if (!this.selectedDevice) return;

        const wager = this.totalWagerHours;
        if (this.totalWagerEl) {
            this.totalWagerEl.innerText = wager >= 1 ? `${wager.toFixed(1)}h` : `${Math.round(wager * 60)}m`;
        }

        // Show/hide glowing "SPIN" tooltip on wheel center
        if (this.wheelSpinHint) {
            if (wager > 0 && !this.wheel.isSpinning) {
                this.wheelSpinHint.classList.remove('opacity-0');
                this.wheelSpinHint.classList.add('opacity-100');
            } else {
                this.wheelSpinHint.classList.remove('opacity-100');
                this.wheelSpinHint.classList.add('opacity-0');
            }
        }
    }

    async executeSpin() {
        if (!this.selectedDevice || this.currentBets.length === 0 || this.wheel.isSpinning) return;

        try {
            const response = await fetch('/api/spin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_mac: this.selectedDevice.mac,
                    bets: this.currentBets
                })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || 'Spin error occurred');
                this.updateWagerHUD();
                return;
            }

            const spinData = await response.json();

            // Trigger canvas wheel physics animation
            this.wheel.spinTo(spinData.winning_number, 5200, () => {
                this.onSpinAnimationComplete(spinData);
            });

        } catch (e) {
            alert('Spin error: ' + e.message);
            this.updateWagerHUD();
        }
    }

    onSpinAnimationComplete(spinData) {
        this.table.clearBets();

        this.selectedDevice.remaining_seconds = spinData.balance_after_hours * 3600.0;
        this.selectedDevice.remaining_hours = spinData.balance_after_hours;
        this.selectedDevice.remaining_formatted = spinData.balance_after_formatted;
        this.selectedDevice.status = spinData.status;

        this.updateDeviceHUD();
        this.fetchRecentNumbers();

        if (spinData.is_busted) {
            if (window.casinoAudio) window.casinoAudio.playBustSound();
            document.getElementById('bustBlackoutModal')?.classList.remove('hidden');
        } else if (spinData.net_profit_hours > 0) {
            if (window.casinoAudio) window.casinoAudio.playWinFanfare();
            if (window.confetti) {
                window.confetti({ particleCount: 110, spread: 80, origin: { y: 0.6 } });
            }
            this.showOutcomeModal(spinData);
        } else {
            this.showOutcomeModal(spinData);
        }
    }

    showOutcomeModal(spinData) {
        const modal = document.getElementById('outcomeModal');
        const numBadge = document.getElementById('outcomeNumberBadge');
        const titleEl = document.getElementById('outcomeTitle');
        const msgEl = document.getElementById('outcomeMessage');
        const detailsEl = document.getElementById('outcomeDetails');

        let colorClass = 'bg-zinc-950 border-zinc-700 text-white';
        if (spinData.winning_color === 'red') colorClass = 'bg-rose-600 border-rose-400 text-white';
        if (spinData.winning_color === 'green') colorClass = 'bg-emerald-600 border-emerald-400 text-white';

        numBadge.className = `w-24 h-24 rounded-full flex items-center justify-center font-black text-4xl border-4 shadow-2xl ${colorClass}`;
        numBadge.innerText = spinData.winning_number;

        if (spinData.net_profit_hours > 0) {
            titleEl.innerHTML = '<span class="text-amber-400 font-black">🎉 WINNER! 🎉</span>';
            msgEl.innerHTML = `<div class="text-emerald-400 font-bold text-lg">+${spinData.net_profit_hours.toFixed(1)} Hours Added to Wi-Fi Balance!</div>`;
        } else {
            titleEl.innerHTML = '<span class="text-zinc-300 font-bold">House Wins</span>';
            msgEl.innerHTML = `<div class="text-zinc-400 text-sm">Lost ${Math.abs(spinData.net_profit_hours).toFixed(1)} hours this round.</div>`;
        }

        detailsEl.innerHTML = `
            <div class="flex justify-between py-1 border-b border-emerald-950">
                <span class="text-zinc-400">Winning Pocket:</span>
                <span class="font-bold text-zinc-100">${spinData.winning_number} (${spinData.winning_color.toUpperCase()})</span>
            </div>
            <div class="flex justify-between py-1 border-b border-emerald-950">
                <span class="text-zinc-400">Total Wager:</span>
                <span class="font-bold text-amber-400">${spinData.total_wager_hours.toFixed(1)}h</span>
            </div>
            <div class="flex justify-between py-1">
                <span class="text-zinc-400">New Wi-Fi Balance:</span>
                <span class="font-bold text-amber-400">${spinData.balance_after_formatted}</span>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    async emergencyUnblock(mac) {
        try {
            await fetch(`/api/devices/${mac}/emergency-unblock`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hours_to_add: 24.0, reason: 'Admin Pardon' })
            });
            await this.fetchMyDevice();
            alert('Wi-Fi connection restored with 24 hours!');
        } catch (e) {
            alert('Unblock error: ' + e.message);
        }
    }

    async fetchRecentNumbers() {
        try {
            const res = await fetch('/api/bets/history');
            const data = await res.json();
            if (this.recentNumbersList && data.recent_numbers) {
                let html = '';
                data.recent_numbers.slice(0, 8).forEach(n => {
                    const col = n === 0 ? 'bg-emerald-600' : (this.table.redNumbers.has(n) ? 'bg-rose-600' : 'bg-zinc-950');
                    html += `<span class="px-2 py-0.5 rounded text-xs font-bold text-white shadow ${col}">${n}</span>`;
                });
                this.recentNumbersList.innerHTML = html;
            }
        } catch (e) {}
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.app = new RouletteApp();
});
