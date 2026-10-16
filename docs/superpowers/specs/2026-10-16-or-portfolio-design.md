# OR Portfolio Site — Design

## Intent
Personal English-language portfolio for a T-shaped operations-research profile:
deep in mathematical optimization, broad in data analysis / ML / engineering.
Readers: hiring managers and graduate admissions committees.
Each project takes a real public dataset (Kaggle / open data), analyzes it, and solves an optimization problem on top.

## Scope (v1)
- Site skeleton + case-study template only. The author fills in real projects later.
- One template project containing writing guidance instead of lorem ipsum.
- Out of scope: backend, auth, blog, comments, i18n, interactive demos (add when needed).

## Approach
Astro static site, Markdown/MDX content collections, KaTeX for math, built-in code highlighting.
Deploy: GitHub Pages workflow. Location: `~/Developer/or-portfolio` (separate from the Instagram project).
Rejected: Next.js (overkill for v1), Jupyter Book/Quarto (weak control over design).

## Pages
- Home: one-line intro, T-shape graphic (depth = optimization; breadth = analytics, ML, engineering), featured projects.
- Projects: list with tag filters (domain, method).
- Project detail: case study.
- About: background and contact.

## Case-study template
1. Business problem
2. Data (source, link, license)
3. EDA
4. Prediction / forecasting (optional)
5. Optimization model (variables, objective, constraints, math, solver)
6. Results & sensitivity
7. Limitations
8. Reproduce (repo link)

Frontmatter: `title`, `domain`, `data_source`, `methods`, `solver`, `tags`, `repo`, `date`.

## Design
Clean, minimal, dark-mode support, responsive down to phone width.

## Verification
`astro build` passes; home, projects list, template project, about render in a headless browser without console errors.
