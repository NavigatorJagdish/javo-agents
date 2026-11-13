import { create } from 'zustand';

export type ContentType = 'video' | 'image' | 'carousel' | 'post' | 'audio';
export type ContentStatus = 'draft' | 'ready' | 'scheduled' | 'simulated' | 'published';

export interface ContentItem {
  id: string;
  title: string;
  type: ContentType;
  status: ContentStatus;
  publishMode?: 'mock' | 'live';
  platform: 'YouTube' | 'Instagram' | 'Facebook' | 'TikTok' | 'X';
  folder: string;
  duration?: string;
  size: string;
  scheduledAt?: string;
  tags: string[];
  aiScore: number;
  caption: string;
  createdAt: string;
}

const INITIAL_CONTENT: ContentItem[] = [
  {
    id: 'cnt-1',
    title: '5 Local AI Workflows That Save 12 Hours/Week',
    type: 'video',
    status: 'scheduled',
    platform: 'YouTube',
    folder: 'D:/CreatorContent/Ready/Reels',
    duration: '00:58',
    size: '48.2 MB',
    scheduledAt: '2026-11-13 18:00',
    tags: ['AI Automation', 'Productivity', 'Local LLM'],
    aiScore: 94,
    caption: 'Run 29 specialized agents locally on Windows with zero cloud lock-in.',
    createdAt: '2026-11-11',
  },
  {
    id: 'cnt-2',
    title: 'Midnight Studio Setup Carousel',
    type: 'carousel',
    status: 'ready',
    platform: 'Instagram',
    folder: 'D:/CreatorContent/Exports/Carousels',
    size: '14.6 MB',
    tags: ['Design System', 'Desk Setup', 'Creator Tech'],
    aiScore: 91,
    caption: '6 slides breaking down lighting, audio chain, and autonomous publishing.',
    createdAt: '2026-11-12',
  },
  {
    id: 'cnt-3',
    title: 'Privacy-First Agent Architecture Deep Dive',
    type: 'post',
    status: 'published',
    platform: 'X',
    folder: 'D:/CreatorContent/Threads',
    size: '18 KB',
    scheduledAt: '2026-11-10 14:30',
    tags: ['Privacy', 'Architecture', 'Agents'],
    aiScore: 89,
    caption: 'How our Privacy Firewall classifies PII before any model call leaves localhost.',
    createdAt: '2026-11-10',
  },
  {
    id: 'cnt-4',
    title: 'Voice Mode Command Demo Clip',
    type: 'video',
    status: 'draft',
    platform: 'Instagram',
    folder: 'D:/CreatorContent/Raw/VoiceDemos',
    duration: '00:41',
    size: '32.9 MB',
    tags: ['Voice AI', 'Whisper', 'Demo'],
    aiScore: 86,
    caption: 'Push-to-talk directly to your agent swarm to schedule and approve posts.',
    createdAt: '2026-11-12',
  },
  {
    id: 'cnt-5',
    title: 'Weekly Creator Growth Breakdown Audio',
    type: 'audio',
    status: 'ready',
    platform: 'YouTube',
    folder: 'D:/CreatorContent/Audio',
    duration: '04:12',
    size: '9.4 MB',
    tags: ['Podcast', 'Growth', 'Analytics'],
    aiScore: 88,
    caption: 'Synthesized executive summary from Weekly Analyst Agent #19.',
    createdAt: '2026-11-09',
  },
  {
    id: 'cnt-6',
    title: 'Q4 Content Pillars Visual Map',
    type: 'image',
    status: 'scheduled',
    platform: 'Facebook',
    folder: 'D:/CreatorContent/Graphics',
    size: '4.1 MB',
    scheduledAt: '2026-11-14 11:00',
    tags: ['Strategy', 'Q4', 'Branding'],
    aiScore: 92,
    caption: 'Visual breakdown of our 4 core educational content pillars for Q4.',
    createdAt: '2026-11-11',
  },
];

interface ContentState {
  assets: ContentItem[];
  addAsset: (item: Omit<ContentItem, 'id' | 'createdAt'>) => void;
  updateStatus: (id: string, status: ContentStatus, scheduledAt?: string) => void;
}

export const useContentStore = create<ContentState>((set) => ({
  assets: INITIAL_CONTENT,
  addAsset: (item) =>
    set((state) => ({
      assets: [
        {
          ...item,
          id: `cnt-${Date.now()}`,
          createdAt: new Date().toISOString().slice(0, 10),
        },
        ...state.assets,
      ],
    })),
  updateStatus: (id, status, scheduledAt) =>
    set((state) => ({
      assets: state.assets.map((asset) =>
        asset.id === id
          ? { ...asset, status, scheduledAt: scheduledAt ?? asset.scheduledAt }
          : asset
      ),
    })),
}));
