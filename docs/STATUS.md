# Status (2026-10-17)

## What exists
Astro static portfolio for OR case studies, branch `feat/portfolio-site` (NOT merged to `main`; `main` has only spec + plan).
Pages: Home (hero, scroll-into-view T animation, latest projects), Projects (tag filter), project case study (+KaTeX), About.
One template case study: `src/content/projects/template-case-study.md` (8 sections, frontmatter: title, domain, data_source{name,url,license}, methods, solver, tags, repo, date).
Design: Apple/Toss-inspired (big bold type, white/dark, Toss blue accent, flat surfaces, spring animation). Earlier glassmorphism/scroll-scrub versions are in git history.
T graphic: `src/components/TShape.astro` (HTML shape; stem grows via grid-rows; fillets via radial-gradient; plays once via IntersectionObserver; reduced-motion/no-JS shows final state).

## Run / test
`npm install && npm run dev` · `npm test` (6 tests) · `npm run test:base` · `npm run test:edge`
Preview used in session: `npm run build && npx astro preview --port 4321`.

## Not done / next
- Merge `feat/portfolio-site` into `main` (ask user) and push to GitHub (no remote yet); Settings → Pages → Source: GitHub Actions.
- Fill `src/site.ts` (name is a placeholder `Inhan`; email/github empty).
- First real project case study (user chose "skeleton only" for v1; topic not chosen).
- Light mode and mobile animation not visually verified; fillet radius is subtle (24px).
- Final review was a self-review (no independent reviewer). `npm audit` shows transitive advisories.
- Docs: spec `docs/superpowers/specs/2026-10-16-or-portfolio-design.md`, plan `docs/superpowers/plans/2026-10-16-or-portfolio.md` (spec still says "Markdown/MDX" and glass design; implementation is .md only and Apple/Toss style).
- Ledger/workspace `.superpowers/` is git-ignored scratch; safe to delete.
