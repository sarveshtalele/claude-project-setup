---
name: brief
description: Create PROJECT-BRIEF.md, the single requirements file the user edits by hand before bootstrap. Use when starting a new project, when the user asks for a requirements or brief template, or when bootstrap finds no brief.
---

# Brief

1. If `PROJECT-BRIEF.md` already exists, don't overwrite it. Show which sections are empty and stop.
2. Otherwise copy the template, after the user confirms the file name (the default is `PROJECT-BRIEF.md` in the project root):
   ```bash
   python3 -c "import shutil,sys; shutil.copyfile(sys.argv[1], 'PROJECT-BRIEF.md')" "${CLAUDE_PLUGIN_ROOT}/templates/PROJECT-BRIEF.md"
   ```
3. If the user pasted requirements into the chat, offer to place them into the matching sections **verbatim**: one numbered requirement per goal, splitting compound sentences. Don't invent requirements or fill sections they left empty; those become interview questions.
4. Tell the user to edit the file in their editor, then run `/claude-project-setup:bootstrap`.

Explain the sections in two lines at most. The template's comments already explain each one.
