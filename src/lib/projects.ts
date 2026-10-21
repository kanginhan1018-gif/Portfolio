import { getCollection } from 'astro:content';

/** Public (non-draft) projects, newest first. */
export const getProjects = async () =>
  (await getCollection('projects', (p) => !p.data.draft)).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
