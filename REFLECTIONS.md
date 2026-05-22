# Reflections - g1-costctl

### 1. AI assistance
**Prompt:** What fraction of code came from AI tools (Claude / Cursor / Copilot) unmodified? Which parts did you actively modify, why?

**Answer:** While I used Gemini CLI to generate the initial logic blocks, I led the implementation step-by-step to ensure I understood every part. I actively modified the code to match the strict test specifications, especially regarding string matching (e.g., "Terminated" vs "Success") and ensuring function signatures like `force` were consistent across the dispatcher. I treated the AI as a junior partner, while I handled the orchestration and verification.

### 2. `clean --apply` blast radius
**Prompt:** If you accidentally ran `clean --tag Environment=dev --apply` in an account shared with another team, what would you have wanted in place to limit damage?

**Answer:** I would rely on the "dry-run" safety feature I implemented as the first line of defense. To further limit damage in a shared account, I would want a "Resource Protection" list that ignores specific IDs, and a mandatory confirmation prompt even when `--apply` is used, unless a secondary `--i-know-what-i-am-doing` flag is provided.
