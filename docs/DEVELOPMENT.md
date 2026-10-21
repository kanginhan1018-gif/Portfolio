# Site development notes

Static portfolio for operations-research case studies (Astro).

- Develop: `npm install && npm run dev`
- Test: `npm test` (build + page checks), `npm run test:base`, `npm run test:edge`
- Add a project: copy `src/content/projects/template-case-study.md`, change the filename and frontmatter, rewrite the 8 sections.
- Edit name/contact: `src/site.ts`.
- Deploy: push to `main` on GitHub, then Settings → Pages → Source: GitHub Actions. If the repo is named `<user>.github.io`, delete the `BASE_PATH` line in the workflow.
