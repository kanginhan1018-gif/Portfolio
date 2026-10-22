import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    domain: z.string(),
    data_source: z.object({ name: z.string(), url: z.string().url(), license: z.string() }),
    methods: z.array(z.string()).min(1),
    solver: z.string(),
    tags: z.array(z.string()),
    repo: z.string().url(),
    date: z.coerce.date(),
    draft: z.boolean().default(false),
    charts: z.array(z.enum(['gap', 'time', 'tradeoff'])).default([]),
  }),
});

// Korean translations, keyed by the same id as the English entry. Only translated fields;
// data_source/solver/repo/date/charts always come from the English entry.
const projectsKo = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects-ko' }),
  schema: z.object({
    title: z.string(),
    domain: z.string(),
    methods: z.array(z.string()).min(1),
    tags: z.array(z.string()),
  }),
});

// Paper reviews: Korean-only blog-style posts, optionally with a slide deck served from public/.
const papers = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/papers' }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    tags: z.array(z.string()),
    date: z.coerce.date(),
    slides: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { projects, projectsKo, papers };
