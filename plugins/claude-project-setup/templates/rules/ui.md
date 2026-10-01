---
paths:
{{UI_PATHS|yamllist}}
---
# UI rules (loaded only when touching UI code)
- Reuse existing components and design tokens before creating new ones. Search first.
- Every interactive element is keyboard-reachable and has an accessible name.
- No hard-coded colours, spacing or copy where the project has tokens or i18n.
- UI changes are verified by the `ui-verifier` agent (real browser), not by reading code.
- Screenshots and recordings go to the outputs folder outside the repo.
