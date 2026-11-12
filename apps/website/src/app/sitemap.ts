import type { MetadataRoute } from 'next';
import { SITE_CONFIG } from '@/data/site';

export const dynamic = 'force-static';

const ROUTES = [
  '',
  '/features',
  '/agents',
  '/how-it-works',
  '/download',
  '/integrations',
  '/voice',
  '/workflows',
  '/security',
  '/pricing',
  '/docs',
  '/changelog',
  '/roadmap',
  '/faq',
  '/contact',
  '/privacy',
  '/terms',
  '/license',
  '/security-reporting',
];

export default function sitemap(): MetadataRoute.Sitemap {
  return ROUTES.map((route) => ({
    url: `${SITE_CONFIG.websiteUrl}${route}/`,
    lastModified: new Date('2026-11-12'),
    changeFrequency: 'weekly',
    priority: route === '' ? 1 : 0.7,
  }));
}
