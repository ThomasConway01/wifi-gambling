/**
 * Clean & Luxurious Felt Betting Zones with Draggable Wi-Fi Tokens
 * Replaces the cluttered 36-number grid with clean, high-impact felt betting spots:
 * - RED (2X)
 * - BLACK (2X)
 * - GREEN 0 (36X)
 * - EVEN & ODD (2X)
 */

class RouletteTable {
    constructor(containerId, onBetsChanged) {
        this.container = document.getElementById(containerId);
        this.onBetsChanged = onBetsChanged;

        this.selectedTokenHours = 1.0;
        this.activeBets = {}; // spotId -> { bet_type, bet_selection, wager_hours }

        this.redNumbers = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);
        this.currentDevice = null;

        this.renderTable();
        this.setupDragAndDrop();
    }

    setDevice(device) {
        this.currentDevice = device;
        this.validateBetsAgainstBalance();
        this.notifyChange();
    }

    setSelectedToken(hours) {
        this.selectedTokenHours = hours;
        document.querySelectorAll('.draggable-token').forEach(el => {
            el.classList.toggle('selected', el.dataset.value === hours.toString());
        });
    }

    clearBets() {
        this.activeBets = {};
        this.updatePlacedTokens();
        this.notifyChange();
    }

    placeBet(spotId, betType, betSelection, hours = null) {
        if (!this.currentDevice) return;

        const maxHours = this.currentDevice.remaining_hours || 0;
        if (maxHours <= 0) return;

        const tokenVal = hours !== null ? hours : this.selectedTokenHours;
        let wagerToAdd = 0;

        if (tokenVal === 'all_in') {
            const otherWagers = this.getTotalWagerHours() - (this.activeBets[spotId]?.wager_hours || 0);
            wagerToAdd = Math.max(0, maxHours - otherWagers);
            if (wagerToAdd <= 0) return;
            this.activeBets[spotId] = {
                bet_type: betType,
                bet_selection: betSelection,
                wager_hours: wagerToAdd
            };
        } else {
            wagerToAdd = parseFloat(tokenVal);
            const currentTotal = this.getTotalWagerHours();
            if (currentTotal + wagerToAdd > maxHours) {
                wagerToAdd = Math.max(0, maxHours - currentTotal);
                if (wagerToAdd <= 0) return;
            }

            if (!this.activeBets[spotId]) {
                this.activeBets[spotId] = {
                    bet_type: betType,
                    bet_selection: betSelection,
                    wager_hours: 0
                };
            }
            this.activeBets[spotId].wager_hours = Math.round((this.activeBets[spotId].wager_hours + wagerToAdd) * 100) / 100;
        }

        this.updatePlacedTokens();
        this.notifyChange();

        if (window.casinoAudio) {
            window.casinoAudio.playChipSound();
            if (this.getTotalWagerHours() >= maxHours * 0.5) {
                window.casinoAudio.playHeartbeat();
            }
        }
    }

    removeBet(spotId) {
        if (this.activeBets[spotId]) {
            delete this.activeBets[spotId];
            this.updatePlacedTokens();
            this.notifyChange();
            if (window.casinoAudio) window.casinoAudio.playChipSound();
        }
    }

    getTotalWagerHours() {
        return Object.values(this.activeBets).reduce((acc, b) => acc + b.wager_hours, 0);
    }

    validateBetsAgainstBalance() {
        if (!this.currentDevice) return;
        const max = this.currentDevice.remaining_hours || 0;
        if (this.getTotalWagerHours() > max) {
            this.clearBets();
        }
    }

    notifyChange() {
        if (this.onBetsChanged) {
            const betsList = Object.values(this.activeBets).map(b => ({
                bet_type: b.bet_type,
                bet_selection: b.bet_selection.toString(),
                wager_hours: b.wager_hours,
                wager_seconds: b.wager_hours * 3600.0
            }));
            this.onBetsChanged(betsList, this.getTotalWagerHours());
        }
    }

    updatePlacedTokens() {
        this.container.querySelectorAll('.placed-token-badge').forEach(b => b.remove());
        this.container.querySelectorAll('.bet-cell').forEach(c => c.classList.remove('has-bet'));

        for (const spotId in this.activeBets) {
            const bet = this.activeBets[spotId];
            const cell = document.getElementById(`spot_${spotId}`);
            if (cell) {
                cell.classList.add('has-bet');
                const badge = document.createElement('div');
                badge.className = 'placed-token-badge';
                badge.innerText = bet.wager_hours >= 1 ? `${Math.round(bet.wager_hours)}h` : `${Math.round(bet.wager_hours * 60)}m`;
                cell.appendChild(badge);
            }
        }
    }

    setupDragAndDrop() {
        let draggedTokenVal = null;
        let dragClone = null;

        const startDrag = (val, e) => {
            draggedTokenVal = val;
            if (window.casinoAudio) window.casinoAudio.playChipSound();

            dragClone = document.createElement('div');
            dragClone.className = 'dragging-token-clone ' + (val === 'all_in' ? 'token-allin' : `token-${val >= 1 ? Math.round(val) + 'h' : '15m'}`);
            dragClone.innerText = val === 'all_in' ? 'MAX' : (val >= 1 ? `${Math.round(val)}h` : '15m');
            document.body.appendChild(dragClone);

            moveDrag(e);
        };

        const moveDrag = (e) => {
            if (!dragClone) return;
            const x = e.clientX || (e.touches && e.touches[0].clientX);
            const y = e.clientY || (e.touches && e.touches[0].clientY);
            dragClone.style.left = `${x}px`;
            dragClone.style.top = `${y}px`;

            document.querySelectorAll('.bet-cell').forEach(c => c.classList.remove('drag-hover'));
            const elem = document.elementFromPoint(x, y);
            const cell = elem ? elem.closest('.bet-cell') : null;
            if (cell) {
                cell.classList.add('drag-hover');
            }
        };

        const endDrag = (e) => {
            if (!dragClone) return;
            const x = e.clientX || (e.changedTouches && e.changedTouches[0].clientX);
            const y = e.clientY || (e.changedTouches && e.changedTouches[0].clientY);

            const elem = document.elementFromPoint(x, y);
            const cell = elem ? elem.closest('.bet-cell') : null;
            if (cell) {
                const spotId = cell.id.replace('spot_', '');
                const type = cell.dataset.type;
                const sel = cell.dataset.sel;
                this.placeBet(spotId, type, sel, draggedTokenVal);
            }

            document.querySelectorAll('.bet-cell').forEach(c => c.classList.remove('drag-hover'));
            dragClone.remove();
            dragClone = null;
            draggedTokenVal = null;
        };

        document.querySelectorAll('.draggable-token').forEach(token => {
            token.addEventListener('pointerdown', (e) => {
                const val = token.dataset.value === 'all_in' ? 'all_in' : parseFloat(token.dataset.value);
                this.setSelectedToken(val);
                startDrag(val, e);
                window.addEventListener('pointermove', moveDrag);
                window.addEventListener('pointerup', function onUp(evt) {
                    endDrag(evt);
                    window.removeEventListener('pointermove', moveDrag);
                    window.removeEventListener('pointerup', onUp);
                });
            });
        });
    }

    renderTable() {
        // Clean, luxurious betting zones (No cluttered 36 grid buttons!)
        let html = `
        <div class="text-white select-none w-full max-w-xl mx-auto flex flex-col gap-4">
            
            <!-- Big Red & Black Betting Zones -->
            <div class="grid grid-cols-2 gap-5 w-full">
                <!-- RED (DOUBLE TIME) -->
                <div id="spot_color_red" 
                     class="bet-cell h-40 sm:h-48 rounded-3xl bg-gradient-to-br from-rose-600 via-rose-700 to-rose-900 border-4 border-rose-400/90 shadow-2xl shadow-rose-950/80 flex flex-col items-center justify-center p-6 text-center cursor-pointer transition transform hover:scale-[1.02]"
                     data-type="color" data-sel="red" title="Drop token here: RED (2X Double Your Time)">
                    <div class="text-3xl sm:text-4xl font-casino font-black tracking-widest text-white drop-shadow-lg">
                        RED
                    </div>
                    <div class="text-xs sm:text-sm font-black font-casino text-rose-200 mt-1 uppercase tracking-wider bg-rose-950/60 px-3 py-1 rounded-full border border-rose-500/40">
                        PAYS 2X (DOUBLE)
                    </div>
                    <div class="text-[11px] text-rose-300/80 font-mono mt-2">Drop Token Here</div>
                </div>

                <!-- BLACK (DOUBLE TIME) -->
                <div id="spot_color_black" 
                     class="bet-cell h-40 sm:h-48 rounded-3xl bg-gradient-to-br from-zinc-900 via-zinc-950 to-black border-4 border-zinc-600 shadow-2xl shadow-black/90 flex flex-col items-center justify-center p-6 text-center cursor-pointer transition transform hover:scale-[1.02]"
                     data-type="color" data-sel="black" title="Drop token here: BLACK (2X Double Your Time)">
                    <div class="text-3xl sm:text-4xl font-casino font-black tracking-widest text-white drop-shadow-lg">
                        BLACK
                    </div>
                    <div class="text-xs sm:text-sm font-black font-casino text-zinc-300 mt-1 uppercase tracking-wider bg-zinc-900/80 px-3 py-1 rounded-full border border-zinc-700">
                        PAYS 2X (DOUBLE)
                    </div>
                    <div class="text-[11px] text-zinc-400 font-mono mt-2">Drop Token Here</div>
                </div>
            </div>

            <!-- Secondary High-Stakes Zones: EVEN, GREEN 0 (JACKPOT), ODD -->
            <div class="grid grid-cols-3 gap-3 w-full">
                <!-- EVEN -->
                <div id="spot_parity_even" 
                     class="bet-cell h-20 rounded-2xl bg-emerald-950/90 hover:bg-emerald-900 border-2 border-emerald-500/80 shadow-lg flex flex-col items-center justify-center text-center cursor-pointer transition"
                     data-type="parity" data-sel="even" title="Drop token here: EVEN (2X)">
                    <div class="text-base sm:text-lg font-casino font-black tracking-wider text-white">EVEN</div>
                    <div class="text-[10px] text-emerald-300 font-mono font-bold">2X PAYOUT</div>
                </div>

                <!-- GREEN ZERO (36X JACKPOT) -->
                <div id="spot_straight_0" 
                     class="bet-cell h-20 rounded-2xl bg-gradient-to-b from-emerald-600 to-emerald-800 hover:from-emerald-500 hover:to-emerald-700 border-2 border-emerald-300 shadow-xl shadow-emerald-950 flex flex-col items-center justify-center text-center cursor-pointer transition"
                     data-type="straight" data-sel="0" title="Drop token here: ZERO (36X JACKPOT)">
                    <div class="text-lg sm:text-xl font-casino font-black text-amber-200">0</div>
                    <div class="text-[10px] text-amber-300 font-mono font-extrabold tracking-wider">36X JACKPOT</div>
                </div>

                <!-- ODD -->
                <div id="spot_parity_odd" 
                     class="bet-cell h-20 rounded-2xl bg-emerald-950/90 hover:bg-emerald-900 border-2 border-emerald-500/80 shadow-lg flex flex-col items-center justify-center text-center cursor-pointer transition"
                     data-type="parity" data-sel="odd" title="Drop token here: ODD (2X)">
                    <div class="text-base sm:text-lg font-casino font-black tracking-wider text-white">ODD</div>
                    <div class="text-[10px] text-emerald-300 font-mono font-bold">2X PAYOUT</div>
                </div>
            </div>

        </div>
        `;

        this.container.innerHTML = html;

        // Click to place support
        this.container.querySelectorAll('.bet-cell').forEach(cell => {
            cell.addEventListener('click', (e) => {
                const spotId = cell.id.replace('spot_', '');
                const type = cell.dataset.type;
                const sel = cell.dataset.sel;
                this.placeBet(spotId, type, sel);
            });

            cell.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                const spotId = cell.id.replace('spot_', '');
                this.removeBet(spotId);
            });
        });
    }
}

window.RouletteTable = RouletteTable;
