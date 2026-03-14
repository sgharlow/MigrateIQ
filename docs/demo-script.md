# MigrateIQ Demo Video Script

> Target: 2:55 (5-second buffer under 3:00 max)
> Format: Screen recording with voiceover

---

## [0:00–0:25] THE PROBLEM (25 sec)

**Screen:** Show the repo file tree in GitLab, expand `database/stored-procedures/`

**Narration:**
> "This application runs on Microsoft SQL Server using WideWorldImporters — one of the most feature-rich MSSQL sample databases. It has natively compiled stored procedures, temporal tables, Row-Level Security, full-text search, JSON operations, and memory-optimized types."

**Screen:** Click into `RecordColdRoomTemperatures.sql`, briefly scroll showing `WITH NATIVE_COMPILATION`, `BEGIN ATOMIC`

> "Migrating this to PostgreSQL typically takes weeks and costs tens of thousands in consulting fees. Every stored procedure, every table, every line of application code needs to be manually translated and validated."

---

## [0:25–0:40] THE TRIGGER (15 sec)

**Screen:** Navigate to Issues → New Issue

**Narration:**
> "With MigrateIQ, you just create an issue."

**Screen:** Type title: `Migrate database from Microsoft SQL Server to PostgreSQL`. Click Create.

> "And assign the MigrateIQ agent."

**Screen:** Assign `@migrateiq` service account. Show the assignment.

> "That's it. One issue, one assignment."

---

## [0:40–1:25] THE AGENTS WORK (45 sec)

**Screen:** Show issue page as comments appear in real-time

**Narration:**
> "Four specialized AI agents now execute in sequence. First, the Scanner finds all 19 SQL and TypeScript files and classifies them."

**Screen:** Show Scanner's issue note appearing with the file table

> "The Translator then converts every file — applying over fifty translation rules. Watch it create commits on a migration branch."

**Screen:** Show Translator progress notes: "Translating [3/19]: InsertCustomerOrders.sql..." Show the commit appearing.

> "The Validator analyzes each translation for risks. It flags two critical issues — the natively compiled procedure and a DECOMPRESS function with no direct PostgreSQL equivalent — and five warnings about behavioral differences."

**Screen:** Show Validator's risk report with the red/yellow/green indicators

---

## [1:25–2:10] THE OUTPUT (45 sec)

**Screen:** Navigate to the migration branch, show file diffs

**Narration:**
> "Let's look at what MigrateIQ produced. Here's the migration branch with all translated files."

**Screen:** Open side-by-side diff of `RecordColdRoomTemperatures.sql` — MSSQL on left, PostgreSQL on right

> "The natively compiled procedure — with its ATOMIC block and memory-optimized table parameter — has been translated to standard PL/pgSQL with a composite type array. The Validator correctly flagged this as critical because of the performance implications."

**Screen:** Show the sub-issues list (6 issues created)

> "MigrateIQ created six sub-issues — one for each migration phase: schema, procedures, views, application code, manual review items, and testing."

**Screen:** Click into Phase 5 (Manual Review), show the critical items listed

> "Phase 5 contains every item that needs human attention, with clear recommendations."

**Screen:** Show the merge request

> "And a merge request with a review checklist tied to the validation findings."

---

## [2:10–2:35] THE IMPACT (25 sec)

**Screen:** Show the migration roadmap comment on the parent issue

**Narration:**
> "The migration roadmap estimates effort, maps dependencies, and recommends an execution order. What would normally take a team two to three weeks has been reduced to a five-minute automated analysis."

**Screen:** Show the sustainability report (Green Agent)

> "MigrateIQ also tracks its own energy usage — this migration consumed a fraction of a kilowatt-hour, compared to roughly eight kilowatt-hours for a developer working manually over the same scope."

---

## [2:35–2:55] ARCHITECTURE (20 sec)

**Screen:** Show the architecture diagram (Mermaid rendered or Canva)

**Narration:**
> "MigrateIQ is a multi-agent flow on GitLab Duo, powered by Claude. Four agents — Scanner, Translator, Validator, and Planner — use thirteen GitLab Duo tools to turn a single issue assignment into a complete migration plan."

> "It doesn't just translate. It tells you what could break, creates the plan, and gives you a merge request ready for review."

**Screen:** Show the MigrateIQ logo or title card

> "MigrateIQ. Database Migration Intelligence for GitLab."

---

## Production Notes

### Recording Setup
- Resolution: 1920x1080
- Browser: Chrome or Firefox, GitLab dark theme recommended for visibility
- Font size: Increase GitLab UI zoom to 125% for readability
- Record screen + mic simultaneously, or record screen then add voiceover

### Voiceover Options
- Record naturally (preferred for authenticity)
- Or use ElevenLabs for consistent pacing

### Pre-Recording Checklist
- [ ] Fresh GitLab project with demo repo pushed
- [ ] MigrateIQ service account configured
- [ ] Clean issue list (no previous test runs)
- [ ] Test one full run to verify all agent outputs appear
- [ ] Rehearse narration timing with stopwatch

### Key Moments to Capture
1. The assignment trigger (simple, quick)
2. Scanner's file table appearing
3. Translator's commit appearing on the branch
4. Validator's risk report with colored severity indicators
5. Side-by-side diff (most impressive visual moment)
6. Sub-issues list (shows actionable output)
7. Migration roadmap comment

### Editing Tips
- Speed up the "waiting" periods between agent comments (2-3x)
- Keep the side-by-side diff visible for at least 5 seconds
- End on the architecture diagram or a clean title card
