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

            // 2. Poll for suggestions
            const poll = setInterval(async () => {
                const jobResp = await fetch(`/api/jobs/${job_id}`);
                const job = await jobResp.json();
                
                if (job.status === 'awaiting_pick') { 
                    clearInterval(poll); 
                    window.location.href = '/suggestions.html'; 
                } else if (job.status === 'failed') {
                    clearInterval(poll);
                    alert('Job failed: ' + job.error);
                    submitBtn.textContent = 'Analyse Content';
                    submitBtn.disabled = false;
                }
            }, 3000);
        } catch (err) {
            console.error(err);
            alert('Failed to submit job.');
            submitBtn.textContent = 'Analyse Content';
            submitBtn.disabled = false;
        }
    });
});
