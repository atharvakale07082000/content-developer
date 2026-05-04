/* History Logic for Lumina */

const historyGrid = document.getElementById('history-grid');

async function loadHistory() {
    try {
        const resp = await fetch('/api/jobs');
        const jobs = await resp.json();
        renderHistory(jobs);
    } catch (err) {
        console.error("Failed to load history:", err);
        historyGrid.innerHTML = '<p class="text-on-surface-variant font-medium">Failed to load artifacts. Please try again later.</p>';
    }
}

function renderHistory(jobs) {
    if (jobs.length === 0) {
        historyGrid.innerHTML = '<p class="text-on-surface-variant font-medium">No artifacts found. Start a new analysis to build your library.</p>';
        return;
    }

    historyGrid.innerHTML = '';
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = "group cursor-pointer md:col-span-6";
        
        const date = new Date(job.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const formats = job.drafts ? job.drafts.map(d => d.format).join(', ') : (job.suggestions ? job.suggestions.map(s => s.format).join(', ') : 'Pending');

        card.innerHTML = `
            <div class="bg-surface-container-lowest rounded-xl p-8 h-full flex flex-col justify-between border border-transparent hover:border-primary/20 transition-all duration-300 shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                <div>
                    <div class="flex justify-between items-start mb-6">
                        <div class="flex gap-2">
                            <span class="px-3 py-1 bg-tertiary-fixed text-on-tertiary-fixed text-[10px] font-bold uppercase tracking-widest rounded-full">${job.status}</span>
                            <span class="px-3 py-1 bg-surface-container text-on-surface-variant text-[10px] font-bold uppercase tracking-widest rounded-full">${formats}</span>
                        </div>
                        <span class="text-on-surface-variant text-xs font-medium">${date}</span>
                    </div>
                    <h3 class="text-xl font-bold text-on-surface mb-4 group-hover:text-primary transition-colors line-clamp-2">${job.input}</h3>
                    <p class="text-on-surface-variant text-sm leading-relaxed line-clamp-3 mb-6">${job.input}</p>
                </div>
                <div class="flex items-center justify-between pt-6 border-t border-outline-variant/10">
                    <div class="flex -space-x-2">
                        <div class="w-8 h-8 rounded-full border-2 border-surface-container-lowest bg-surface-container-high flex items-center justify-center">
                            <span class="material-symbols-outlined text-xs">person</span>
                        </div>
                        <div class="w-8 h-8 rounded-full border-2 border-surface-container-lowest bg-primary-fixed flex items-center justify-center">
                            <span class="material-symbols-outlined text-xs">robot_2</span>
                        </div>
                    </div>
                    <div class="flex gap-4">
                        <button class="text-on-surface-variant hover:text-primary transition-colors"><span class="material-symbols-outlined text-lg">share</span></button>
                        <button class="text-on-surface-variant hover:text-primary transition-colors"><span class="material-symbols-outlined text-lg">bookmark</span></button>
                        <button class="text-on-surface-variant hover:text-primary transition-colors"><span class="material-symbols-outlined text-lg">arrow_forward</span></button>
                    </div>
                </div>
            </div>
        `;

        card.onclick = () => {
            window.location.href = `/dashboard.html?jobId=${job._id}`;
        };

        historyGrid.appendChild(card);
    });
}

loadHistory();
