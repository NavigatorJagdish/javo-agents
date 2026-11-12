export const SITE_CONFIG = {
  name: 'Javo Agents',
  tagline: 'Your Fully Automated AI Team',
  version: '0.1.0-alpha',
  releaseStatus: 'Private Alpha Test',
  license: 'MIT',
  githubUrl: 'https://github.com/NavigatorJagdish/javo-agents',
  githubReleasesUrl: 'https://github.com/NavigatorJagdish/javo-agents/releases',
  githubActionsUrl: 'https://github.com/NavigatorJagdish/javo-agents/actions',
  githubPrUrl: 'https://github.com/NavigatorJagdish/javo-agents/pull/1',
  githubDiscussionsUrl: 'https://github.com/NavigatorJagdish/javo-agents/discussions',
  githubIssuesUrl: 'https://github.com/NavigatorJagdish/javo-agents/issues',
  websiteUrl: 'https://javoagents.org',
  windowsArtifacts: {
    installerName: 'JavoAgents-0.1.0-x64.exe',
    installerSha256: '5d6f13f07a3b84957814f5a079c8de78ee14bbfbae91eda5764d03df1e8e8fd0',
    installerDownloadUrl: 'https://github.com/NavigatorJagdish/javo-agents/releases/download/untagged-793724ecd9d08a285337/JavoAgents-0.1.0-x64.exe',
    portableName: 'JavoAgents-Portable-0.1.0-x64.exe',
    portableSha256: 'c8e092aa339137d615e474ca0b7ed598f0cc74bd76cca10d82c601620f51b7e7',
    portableDownloadUrl: 'https://github.com/NavigatorJagdish/javo-agents/releases/download/untagged-793724ecd9d08a285337/JavoAgents-Portable-0.1.0-x64.exe',
    checksumsUrl: 'https://github.com/NavigatorJagdish/javo-agents/releases/download/untagged-793724ecd9d08a285337/SHA256SUMS.txt',
    draftReleaseUrl: 'https://github.com/NavigatorJagdish/javo-agents/releases/tag/untagged-793724ecd9d08a285337',
    workflowUrl: 'https://github.com/NavigatorJagdish/javo-agents/actions/workflows/ci-windows.yml',
  },
  androidArtifacts: {
    debugApkName: 'javo-agents-android-v0.1.0-alpha-debug.apk',
    releaseApkName: 'javo-agents-android-v0.1.0-alpha-release-unsigned.apk',
    releaseAabName: 'javo-agents-android-v0.1.0-alpha-release-unsigned.aab',
    workflowUrl: 'https://github.com/NavigatorJagdish/javo-agents/actions/workflows/ci-android.yml',
    actionsRunsUrl: 'https://github.com/NavigatorJagdish/javo-agents/actions?query=workflow%3A%22CI+%E2%80%94+Android+Companion%22',
  },
  windowsMinSpecs: {
    os: 'Windows 10 / 11 (64-bit)',
    ram: '8 GB RAM minimum (16 GB recommended)',
    storage: '10 GB free disk space (plus local Ollama models)',
    runtime: 'Python 3.11+ & Node.js 20+ (or bundled Windows runtime)',
  },
  androidMinSpecs: {
    os: 'Android 10 (API 29) or higher',
    ram: '4 GB RAM minimum',
    storage: '250 MB free storage',
    note: 'Companion app pairs over LAN/TLS with your Windows Local Runtime.',
  },
};

export const NAV_LINKS = [
  { label: 'Features', href: '/features' },
  { label: 'Agents', href: '/agents' },
  { label: 'Workflows', href: '/workflows' },
  { label: 'Voice', href: '/voice' },
  { label: 'Integrations', href: '/integrations' },
  { label: 'Docs', href: '/docs' },
  { label: 'Pricing', href: '/pricing' },
];

export const FOOTER_COLUMNS = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '/features' },
      { label: '29 AI Agents', href: '/agents' },
      { label: 'How It Works', href: '/how-it-works' },
      { label: 'Workflows', href: '/workflows' },
      { label: 'Voice Mode', href: '/voice' },
      { label: 'Integrations', href: '/integrations' },
      { label: 'Download', href: '/download' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '/docs' },
      { label: 'Pricing ($0 Free)', href: '/pricing' },
      { label: 'Changelog', href: '/changelog' },
      { label: 'Public Roadmap', href: '/roadmap' },
      { label: 'FAQ', href: '/faq' },
      { label: 'Contact & Community', href: '/contact' },
    ],
  },
  {
    title: 'Security & Legal',
    links: [
      { label: 'Privacy & Security', href: '/security' },
      { label: 'Security Reporting', href: '/security-reporting' },
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
      { label: 'MIT License', href: '/license' },
    ],
  },
];
