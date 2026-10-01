---
paths:
{{API_PATHS|yamllist}}
---
# API rules (loaded only when touching API code)
- Validate every request body, query and path parameter at the handler boundary.
- Every new endpoint checks authentication *and* authorization, unless the task marks it public.
- Errors return a consistent shape and never leak stack traces or internal IDs.
- Changing a response shape is a breaking change: it needs a version bump or a task noting all consumers.
- Each new endpoint gets at least one test for success and one for rejected input.
