/* Dashboard Logic for Lumina - SSE Driven State Management */

const views = {
    input: document.getElementById('view-input'),
    thinking: document.getElementById('view-thinking'),
    results: document.getElementById('view-results')
};

const components = {
    topicInput: document.getElementById('topic-input'),
    analyzeBtn: document.getElementById('analyze-btn'),
    thinkingStatus: document.getElementById('thinking-status'),
    suggestionsGrid: document.getElementById('suggestions-grid'),
    suggestionsContainer: document.getElementById('suggestions-container'),
    pickBtn: document.getElementById('pick-btn'),
    draftsContainer: document.getElementById('drafts-container'),
    draftsList: document.getElementById('drafts-list'),
    newDraftBtn: document.getElementById('new-draft-btn')
};

let currentJobId = null;
let eventSource = null;
let selectedFormats = new Set();

function switchView(viewName) {
    Object.keys(views).forEach(key => {
        if (key === viewName) views[key].classList.remove('hidden');
        else views[key].classList.add('hidden');
    });
}

async function startAnalysis() {
    const topic = components.topicInput.value.trim();
    if (!topic) return alert("Please enter a topic or objective.");

    switchView('thinking');
    components.thinkingStatus.innerText = "Synthesizing Intent...";

    try {
        const resp = await fetch('/api/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: topic, input_type: 'topic' })
        });
        const data = await resp.json();
        currentJobId = data.job_id;
        setupSSE(currentJobId);
    } catch (err) {
        console.error(err);
        alert("Failed to start analysis.");
        switchView('input');
    }
}

function setupSSE(jobId) {
    if (eventSource) eventSource.close();
    
    eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    eventSource.addEventListener('status_update', (event) => {
        const job = JSON.parse(event.data);
        handleJobUpdate(job);
    });

    eventSource.onerror = (err) => {
        console.error("SSE Error:", err);
        // Fallback to polling if SSE fails
    };
}

function handleJobUpdate(job) {
    const status = job.status;
    
    if (status === 'thinking') {
        components.thinkingStatus.innerText = "Processing Logic Flow...";
    } else if (status === 'awaiting_pick') {
        renderSuggestions(job.suggestions);
        switchView('results');
    } else if (status === 'drafting') {
        switchView('thinking');
        components.thinkingStatus.innerText = "Building Content Blueprints...";
    } else if (status === 'done') {
        renderDrafts(job.drafts);
        switchView('results');
        components.draftsContainer.classList.remove('hidden');
        components.suggestionsContainer.classList.add('hidden');
    } else if (status === 'failed') {
        alert("Job failed: " + (job.error || "Unknown error"));
        switchView('input');
        eventSource.close();
    }
}

function renderSuggestions(suggestions) {
    components.suggestionsGrid.innerHTML = '';
    selectedFormats.clear();
    components.pickBtn.classList.add('hidden');

    suggestions.forEach((s, idx) => {
        const card = document.createElement('div');
        card.className = "bg-surface-container-lowest p-6 rounded-2xl border border-outline-variant/10 hover:shadow-soft-glow transition-all cursor-pointer group flex flex-col justify-between h-full";
        card.innerHTML = `
            <div class="space-y-4">
                <div class="flex justify-between items-start">
                    <div class="w-12 h-12 bg-primary/5 rounded-xl flex items-center justify-center">
                        <span class="material-symbols-outlined text-primary text-2xl">${getIconForFormat(s.format)}</span>
                    </div>
                    <div class="checkbox-ui w-6 h-6 rounded-full border-2 border-outline-variant group-[.selected]:bg-primary group-[.selected]:border-primary flex items-center justify-center transition-all">
                        <span class="material-symbols-outlined text-white text-[14px] scale-0 group-[.selected]:scale-100 transition-transform">check</span>
                    </div>
                </div>
                <div class="space-y-1">
                    <h4 class="font-black text-sm uppercase tracking-widest text-on-surface">${s.format}</h4>
                    <p class="text-[13px] text-on-surface-variant leading-relaxed line-clamp-3">${s.reasoning}</p>
                </div>
            </div>
            <div class="mt-6 pt-4 border-t border-surface-container text-[10px] font-bold uppercase tracking-widest text-outline">
                Editorial Grade Gen
            </div>
        `;

        card.onclick = () => {
            card.classList.toggle('selected');
            if (card.classList.contains('selected')) {
                selectedFormats.add(s.format);
                card.classList.add('ring-2', 'ring-primary', 'ring-offset-2');
            } else {
                selectedFormats.delete(s.format);
                card.classList.remove('ring-2', 'ring-primary', 'ring-offset-2');
            }
            
            if (selectedFormats.size > 0) components.pickBtn.classList.remove('hidden');
            else components.pickBtn.classList.add('hidden');
        };

        components.suggestionsGrid.appendChild(card);
    });
}

function getIconForFormat(format) {
    const f = format.toLowerCase();
    if (f.includes('linkedin')) return 'work';
    if (f.includes('instagram')) return 'photo_camera';
    if (f.includes('newsletter')) return 'mail';
    if (f.includes('blog')) return 'article';
    if (f.includes('twitter') || f.includes('x')) return 'share';
    return 'description';
}

async function submitPicks() {
    if (selectedFormats.size === 0) return;

    switchView('thinking');
    components.thinkingStatus.innerText = "Architecting Drafts...";

    try {
        await fetch(`/api/jobs/${currentJobId}/pick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formats: Array.from(selectedFormats) })
        });
    } catch (err) {
        console.error(err);
        alert("Failed to submit selection.");
        switchView('results');
    }
}

function renderDrafts(drafts) {
    components.draftsList.innerHTML = '';
    drafts.forEach(draft => {
        const item = document.createElement('div');
        item.className = "bg-surface-container-lowest p-10 rounded-[2rem] border border-outline-variant/10 shadow-soft-glow space-y-8 relative overflow-hidden";
        item.innerHTML = `
            <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 -mr-16 -mt-16 rounded-full blur-2xl"></div>
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-primary/5 rounded-xl flex items-center justify-center">
                        <span class="material-symbols-outlined text-primary">${getIconForFormat(draft.format)}</span>
                    </div>
                    <div>
                        <span class="px-3 py-1 bg-tertiary-fixed text-on-tertiary-fixed text-[10px] font-bold uppercase tracking-widest rounded-full">${draft.format}</span>
                    </div>
                </div>
                <button class="text-on-surface-variant hover:text-primary transition-colors">
                    <span class="material-symbols-outlined">content_copy</span>
                </button>
            </div>
            <div class="prose prose-slate max-w-none text-on-surface text-lg leading-[1.8] font-medium selection:bg-primary-container">
                ${draft.content.replace(/\n/g, '<br>')}
            </div>
            <div class="flex items-center gap-4 pt-6 border-t border-surface-container text-[11px] font-bold uppercase tracking-[0.2em] text-outline">
                <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[14px]">verified</span> AI Verified</span>
                <span class="flex items-center gap-1.5"><span class="material-symbols-outlined text-[14px]">auto_awesome</span> Editorial Grade</span>
            </div>
        `;
        components.draftsList.appendChild(item);
    });
}

function exportContent(type) {
    if (!currentJobId) return;
    window.location.href = `/api/jobs/${currentJobId}/export?format=${type}`;
}

// Event Listeners
components.analyzeBtn.onclick = startAnalysis;
components.pickBtn.onclick = submitPicks;
components.newDraftBtn.onclick = () => {
    switchView('input');
    components.topicInput.value = '';
    components.draftsContainer.classList.add('hidden');
    components.suggestionsContainer.classList.remove('hidden');
    if (eventSource) eventSource.close();
};

document.getElementById('export-pdf-btn').onclick = () => exportContent('pdf');
document.getElementById('export-word-btn').onclick = () => exportContent('word');

// Handle direct navigation to results if jobId in URL (optional)
const urlParams = new URLSearchParams(window.location.search);
const jobId = urlParams.get('jobId');
if (jobId) {
    currentJobId = jobId;
    setupSSE(jobId);
    switchView('thinking');
}
