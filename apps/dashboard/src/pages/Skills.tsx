import React, { useState } from 'react';
import { Sparkles, ShieldCheck, ArrowUpCircle, Terminal } from 'lucide-react';
import { Card, Badge, Button, Chip } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface SkillEntry {
  id: string;
  name: string;
  tier: 'core' | 'community' | 'sandbox';
  trustScore: number;
  version: string;
  description: string;
  updateReady?: boolean;
}

const INITIAL_SKILLS: SkillEntry[] = [
  { id: 'sk-1', name: 'ffmpeg_auto_reframe', tier: 'core', trustScore: 100, version: '2.1.0', description: 'Smart 9:16 subject-tracking crop for Shorts and Reels.' },
  { id: 'sk-2', name: 'hook_retention_scorer', tier: 'core', trustScore: 99, version: '1.8.4', description: 'Evaluates opening 3 seconds for pacing, text legibility, and audio punch.' },
  { id: 'sk-3', name: 'youtube_transcript_mining', tier: 'community', trustScore: 94, version: '1.3.0', description: 'Extracts high-signal topic clusters from niche channels.', updateReady: true },
  { id: 'sk-4', name: 'instagram_carousel_pdf', tier: 'community', trustScore: 91, version: '1.0.5', description: 'Renders branded slide decks from Markdown outlines.' },
  { id: 'sk-5', name: 'auto_chapter_marker', tier: 'sandbox', trustScore: 86, version: '0.9.2', description: 'Newly synthesized by Self-Upgrading Engineer (#04); running in isolated sandbox.' },
];

export const Skills: React.FC = () => {
  const [skills, setSkills] = useState(INITIAL_SKILLS);
  const [tier, setTier] = useState('all');
  const addToast = useAppStore((s) => s.addToast);

  const promoteOrUpdate = (id: string) => {
    setSkills((prev) =>
      prev.map((s) =>
        s.id === id
          ? {
              ...s,
              tier: s.tier === 'sandbox' ? 'community' : s.tier,
              trustScore: Math.min(100, s.trustScore + 4),
              updateReady: false,
            }
          : s
      )
    );
    addToast('Skill Pipeline Updated', 'Plugin Trust (#21) verified manifest and capability scopes.', 'success');
  };

  const filtered = skills.filter((s) => tier === 'all' || s.tier === tier);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
          Skills & Sandbox Trust Pipeline
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Every skill is scored by Plugin Trust (#21) and sandbox-tested before promotion to production.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {['all', 'core', 'community', 'sandbox'].map((t) => (
          <Chip
            key={t}
            label={t === 'all' ? 'All Tiers' : t.toUpperCase()}
            selected={tier === t}
            variant={t === 'sandbox' ? 'violet' : 'cyan'}
            onClick={() => setTier(t)}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((skill) => (
          <Card key={skill.id} variant="status" glow={skill.tier === 'sandbox' ? 'violet' : 'cyan'}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 flex items-center justify-center text-[#A78BFA]">
                  {skill.tier === 'sandbox' ? <Terminal className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
                </div>
                <div>
                  <h3 className="text-sm font-mono font-semibold text-slate-900 dark:text-white">
                    {skill.name}
                  </h3>
                  <p className="text-xs text-slate-400">
                    v{skill.version} • {skill.tier.toUpperCase()}
                  </p>
                </div>
              </div>

              <Badge status={skill.trustScore >= 95 ? 'active' : skill.trustScore >= 88 ? 'info' : 'warning'} size="sm">
                Trust {skill.trustScore}/100
              </Badge>
            </div>

            <p className="mt-3 text-xs text-slate-600 dark:text-slate-300">{skill.description}</p>

            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between">
              <span className="inline-flex items-center gap-1 text-xs text-emerald-500">
                <ShieldCheck className="h-3.5 w-3.5" /> Scoped Capabilities
              </span>
              {(skill.updateReady || skill.tier === 'sandbox') && (
                <Button
                  size="sm"
                  variant={skill.tier === 'sandbox' ? 'violet' : 'secondary'}
                  leftIcon={<ArrowUpCircle className="h-3.5 w-3.5" />}
                  onClick={() => promoteOrUpdate(skill.id)}
                >
                  {skill.tier === 'sandbox' ? 'Promote to Verified' : 'Apply Update'}
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
