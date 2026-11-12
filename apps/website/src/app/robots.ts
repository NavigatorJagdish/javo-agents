import type { MetadataRoute } from 'next';
import { SITE_CONFIG } from '@/data/site';

export const dynamic = 'force-static';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: `${SITE_CONFIG.websiteUrl}/sitemap.xml`,
  };
}
