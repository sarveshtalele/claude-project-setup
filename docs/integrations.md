# Integrations: plugins and MCP servers

| Class | Meaning | After approval |
|---|---|---|
| **REUSE** | Installed and fits a need | `enabledPlugins: true`, or the server is already configured |
| **ADD** | Not installed and fills a need | Plugin: each install needs its own yes. MCP: written to `.mcp.json` |
| **SKIP** | Installed but not needed here | Left as is. Add it to `plugins.disable` to turn it off for this project only |
| **CONFLICT** | Two tools doing one exclusive job (e.g. two output-style plugins) | You choose one |

## Capabilities and auto-detection
| Capability | Auto-needed when | Catalog MCP server |
|---|---|---|
| `ui-testing` | A frontend framework is detected | `playwright` (`npx @playwright/mcp@latest`) |
| `library-docs` | Any manifest is present | `context7` (`npx -y @upstash/context7-mcp`) |
| `github` | The git remote host is github.com | `github` (HTTP, `Bearer ${GITHUB_PAT}`, asks before writing) |
| `error-monitoring` | Sentry SDK detected | `sentry` (HTTP; you sign in with `/mcp`) |
| `web-research` | You ask for it | `firecrawl` (`${FIRECRAWL_API_KEY}`, asks) |
| `code-review`, `response-style` | Matched against installed plugin descriptions | (plugins only) |

Plugin suggestions come **only** from your real installed and marketplace listings. Nothing is fetched from the web or invented.

## Secrets
- `.mcp.json` env and header values must be `${VAR}` references. `render.py` **refuses** literal keys (token patterns, or any value without `${`).
- `.env.example` lists the variable names, with no values.
- Claude never enters credentials or completes OAuth. It tells you which variable to set, or to run `/mcp`.

## Permissions
- Catalog servers with `permission: allow` (playwright, context7, sentry) get an `mcp__<name>` allow rule.
- Everything else, including custom servers, gets an **ask** rule.

## Manage later
```text
/claude-project-setup:integrations list
/claude-project-setup:integrations add ui-testing
/claude-project-setup:doctor --tools
```
