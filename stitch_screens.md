# Stitch Screen Prompts

Go to stitch.withgoogle.com, create a project called "Content Strategy Agent",
then create each screen by pasting the prompt below into Stitch.

---

## Screen 1: Submit Job  (route: /)

> A clean minimal web app screen for submitting content to an AI agent.
> Dark mode. Large text input area at top with placeholder "Paste a YouTube URL,
> blog link, or describe a topic...". Below it a prominent "Analyse Content"
> button in indigo/purple. Below the button three small badge icons for the
> supported output formats: LinkedIn, Email Newsletter, Instagram.
> Clean sans-serif font. Subtle card shadow. Centered layout max 640px wide.

---

## Screen 2: Suggestions View  (route: /suggestions)

> A content suggestion results screen for an AI content tool. Dark mode.
> Section titled "AI Suggestions" with 4-6 cards in a vertical list.
> Each card has: a format badge (LinkedIn / Newsletter / Instagram) top-left,
> a bold hook headline, short audience description in muted text, a tone tag,
> and a checkbox on the right to select it.
> Fixed sticky bar at the bottom with "Generate Drafts →" button that activates
> when at least one card is checked.

---

## Screen 3: Drafts View  (route: /drafts)

> A content drafts viewer. Dark mode. Tab interface at top for each format
> (LinkedIn, Newsletter, Instagram). Each tab shows the full draft in a
> readable card. Top-right of each card has a "Copy" button.
> Below the draft a small "Regenerate" link in muted text.

---

## After designing in Stitch

```bash
npx @_davideast/stitch-mcp init
npx @_davideast/stitch-mcp serve -p <your-project-id>   # local preview
npx @_davideast/stitch-mcp site  -p <your-project-id>   # build Astro → copy to /frontend
```

## API wiring (add to Stitch-generated JS)

```js
// 1. Submit job
const { job_id } = await fetch('/api/jobs', {
  method: 'POST', headers: {'Content-Type':'application/json'},
  body: JSON.stringify({ input: userInput })
}).then(r => r.json());

// 2. Poll for suggestions
const poll = setInterval(async () => {
  const job = await fetch(`/api/jobs/${job_id}`).then(r => r.json());
  if (job.status === 'awaiting_pick') { clearInterval(poll); renderSuggestions(job.suggestions); }
}, 3000);

// 3. Submit picks
await fetch(`/api/jobs/${job_id}/pick`, {
  method: 'POST', headers: {'Content-Type':'application/json'},
  body: JSON.stringify({ formats: selectedFormats })
});

// 4. Poll for drafts
const pollDrafts = setInterval(async () => {
  const job = await fetch(`/api/jobs/${job_id}`).then(r => r.json());
  if (job.status === 'done') { clearInterval(pollDrafts); renderDrafts(job.drafts); }
}, 3000);
```
