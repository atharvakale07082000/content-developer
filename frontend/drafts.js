document.addEventListener('DOMContentLoaded', async () => {
    const jobId = localStorage.getItem('current_job_id');
    if (!jobId) {
        window.location.href = '/';
        return;
    }

    const tabsContainer = document.getElementById('tabs-container');
    const draftContentEl = document.getElementById('draft-content');
    const wordCountEl = document.getElementById('word-count');
    const copyBtn = document.getElementById('copy-btn');
    
    let drafts = {};
    let activeFormat = null;

    try {
        const resp = await fetch(`/api/jobs/${jobId}`);
        const job = await resp.json();
        
        if (job.drafts && Object.keys(job.drafts).length > 0) {
            drafts = job.drafts;
            renderTabs();
        } else {
            draftContentEl.textContent = 'No drafts found. Job status: ' + job.status;
        }
    } catch (e) {
        console.error(e);
        draftContentEl.textContent = 'Failed to load drafts.';
    }

    function renderTabs() {
        tabsContainer.innerHTML = '';
        const formats = Object.keys(drafts);
        
        if (formats.length > 0 && !activeFormat) {
            activeFormat = formats[0];
        }

        formats.forEach(format => {
            const isActive = format === activeFormat;
            const btnClass = isActive 
                ? 'flex-1 py-3 text-sm font-medium rounded-lg bg-surface-container-high text-primary transition-all duration-200 shadow-sm'
                : 'flex-1 py-3 text-sm font-medium rounded-lg text-on-surface-variant hover:text-on-surface transition-all duration-200';
            
            const btn = document.createElement('button');
            btn.className = btnClass;
            btn.textContent = format;
            btn.addEventListener('click', () => {
                activeFormat = format;
                renderTabs();
            });
            tabsContainer.appendChild(btn);
        });

        renderDraft();
    }

    function renderDraft() {
        if (!activeFormat || !drafts[activeFormat]) return;
        
        const content = drafts[activeFormat];
        draftContentEl.textContent = content;
        
        const words = content.trim().split(/\\s+/).length;
        wordCountEl.textContent = `Words: ${words}`;
        
        copyBtn.querySelector('span:last-child').textContent = 'Copy';
    }

    copyBtn.addEventListener('click', () => {
        if (!activeFormat || !drafts[activeFormat]) return;
        const text = drafts[activeFormat];
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.querySelector('span:last-child').textContent = 'Copied!';
            setTimeout(() => {
                copyBtn.querySelector('span:last-child').textContent = 'Copy';
            }, 2000);
        });
    });
});
