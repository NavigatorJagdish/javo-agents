/** @type {import('next').NextConfig} */
// GitHub Pages project sites live under /<repository>/, not the domain root.
// Keep local and alternate-host development at /, but bake in the correct
// prefix when the Pages deployment workflow sets GITHUB_PAGES=true.
const isGitHubPages = process.env.GITHUB_PAGES === 'true';

const nextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: isGitHubPages ? '/javo-agents' : undefined,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
