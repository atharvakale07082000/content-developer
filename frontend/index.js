document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submit-job');
    const inputArea = document.getElementById('job-input');

    submitBtn.addEventListener('click', async () => {
        const userInput = inputArea.value.trim();
        if (!userInput) return;

        // Change button state
        submitBtn.textContent = 'Analyzing...';
        submitBtn.disabled = true;

        try {
            // 1. Submit job
            const response = await fetch('/api/jobs', {
                method: 'POST', 
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ input: userInput })
            });
            const { job_id } = await response.json();
            
            localStorage.setItem('current_job_id', job_id);

            // 2. SSE for suggestions
            const eventSource = new EventSource(`/api/jobs/${job_id}/stream`);
            
            eventSource.addEventListener('status_update', (event) => {
                const job = JSON.parse(event.data);
                
                if (job.status === 'awaiting_pick') { 
                    eventSource.close();
                    window.location.href = '/suggestions.html'; 
                } else if (job.status === 'failed') {
                    eventSource.close();
                    alert('Job failed: ' + job.error);
                    submitBtn.textContent = 'Analyse Content';
                    submitBtn.disabled = false;
                }
            });

            eventSource.addEventListener('error', (event) => {
                console.error('SSE Error:', event);
                eventSource.close();
                alert('Connection to analysis stream lost or failed. Please check if the backend is running and try again.');
                submitBtn.textContent = 'Analyse Content';
                submitBtn.disabled = false;
            });
        } catch (err) {
            console.error(err);
            alert('Failed to submit job.');
            submitBtn.textContent = 'Analyse Content';
            submitBtn.disabled = false;
        }
    });
});
