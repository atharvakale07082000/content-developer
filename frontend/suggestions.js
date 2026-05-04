document.addEventListener('DOMContentLoaded', async () => {
    const jobId = localStorage.getItem('current_job_id');
    if (!jobId) {
        window.location.href = '/';
        return;
    }

    const container = document.getElementById('suggestions-container');
    const generateBtn = document.getElementById('generate-drafts');
    
    // Fetch suggestions
    try {
        const resp = await fetch(`/api/jobs/${jobId}`);
        const job = await resp.json();
        
        if (!job.suggestions || Object.keys(job.suggestions).length === 0) {
            container.innerHTML = '<p class="text-on-surface">No suggestions found.</p>';
            return;
        }

        renderSuggestions(job.suggestions);
    } catch (e) {
        console.error(e);
        container.innerHTML = '<p class="text-error">Failed to load suggestions.</p>';
    }

    function renderSuggestions(suggestions) {
        container.innerHTML = '';
        const formats = Object.keys(suggestions);
        
        formats.forEach(format => {
            const suggestion = suggestions[format];
            const html = `
                <div class="group relative bg-surface-container-low p-6 rounded-xl hover:bg-surface-container-high transition-all duration-300">
                    <div class="flex justify-between items-start mb-4">
                        <span class="px-3 py-1 rounded-full bg-surface-container-highest text-primary text-[10px] uppercase tracking-widest font-bold">${format}</span>
                        <input class="platform-checkbox w-6 h-6 rounded-lg bg-surface-container-lowest border-none text-primary-container focus:ring-offset-surface ring-offset-2 focus:ring-primary" type="checkbox" value="${format}">
                    </div>
                    <h3 class="text-xl font-bold tracking-tight mb-2 group-hover:text-primary transition-colors">${suggestion.headline || 'Generated hook'}</h3>
                    <p class="text-on-surface-variant text-sm mb-4 leading-relaxed">${suggestion.audience || 'Target audience description'}</p>
                    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-lg border border-outline-variant/15 text-on-surface-variant text-xs font-medium italic">
                        <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
                        ${suggestion.tone || 'Professional'}
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', html);
        });

        // Add event listeners to checkboxes
        const checkboxes = document.querySelectorAll('.platform-checkbox');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', updateGenerateButton);
        });
        updateGenerateButton();
    }

    function updateGenerateButton() {
        const checked = document.querySelectorAll('.platform-checkbox:checked').length;
        generateBtn.disabled = checked === 0;
    }

    generateBtn.addEventListener('click', async () => {
        const selectedFormats = Array.from(document.querySelectorAll('.platform-checkbox:checked')).map(cb => cb.value);
        if (selectedFormats.length === 0) return;

        generateBtn.textContent = 'Generating...';
        generateBtn.disabled = true;

        try {
            await fetch(`/api/jobs/${jobId}/pick`, {
                method: 'POST', 
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ formats: selectedFormats })
            });

            // 2. SSE for drafts
            const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);
            
            eventSource.addEventListener('status_update', (event) => {
                const job = JSON.parse(event.data);
                
                if (job.status === 'done') { 
                    eventSource.close();
                    window.location.href = '/drafts.html'; 
                } else if (job.status === 'failed') {
                    eventSource.close();
                    alert('Draft generation failed');
                    generateBtn.textContent = 'Generate Drafts';
                    generateBtn.disabled = false;
                }
            });

            eventSource.addEventListener('error', (event) => {
                console.error('SSE Error:', event);
                eventSource.close();
                alert('Connection to drafting stream lost. Please try again.');
                generateBtn.textContent = 'Generate Drafts';
                generateBtn.disabled = false;
            });
        } catch (e) {
            console.error(e);
            alert('Failed to submit picks');
            generateBtn.textContent = 'Generate Drafts';
            generateBtn.disabled = false;
        }
    });
});
