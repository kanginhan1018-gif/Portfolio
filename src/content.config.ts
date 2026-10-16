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
  }),
});

export const collections = { projects };
