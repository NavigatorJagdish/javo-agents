import React, { useState } from 'react';
import { Youtube, Instagram, Facebook, Twitter, Plus, RefreshCw, ShieldCheck, Palette } from 'lucide-react';
import { Card, Badge, Button, Chip, Modal } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface SocialAccount {
  id: string;
  platform: 'YouTube' | 'Instagram' | 'Facebook' | 'X';
  handle: string;
  followers: string;
  status: 'connected' | 'expiring';
  cadenceCap: string;
  brandVoice: string;
}

const INITIAL_ACCOUNTS: SocialAccount[] = [
  { id: 'acc-1', platform: 'YouTube', handle: '@JavoTechStudio', followers: '37.4K', status: 'connected', cadenceCap: '2 Shorts / day', brandVoice: 'Technical & Energetic' },
  { id: 'acc-2', platform: 'Instagram', handle: '@javo.ai', followers: '24.8K', status: 'connected', cadenceCap: '2 Reels / day', brandVoice: 'Clean Visual Storytelling' },
  { id: 'acc-3', platform: 'Facebook', handle: 'Javo Creator Lab', followers: '11.2K', status: 'connected', cadenceCap: '1 Post / day', brandVoice: 'Educational Deep-Dives' },
  { id: 'acc-4', platform: 'X', handle: '@javo_agents', followers: '18.9K', status: 'expiring', cadenceCap: '4 Threads / day', brandVoice: 'Sharp Concise Insights' },
];

const platformIcon = {
  YouTube: <Youtube className="h-5 w-5 text-red-500" />,
  Instagram: <Instagram className="h-5 w-5 text-pink-500" />,
  Facebook: <Facebook className="h-5 w-5 text-blue-500" />,
  X: <Twitter className="h-5 w-5 text-sky-400" />,
};

export const Accounts: React.FC = () => {
  const [accounts, setAccounts] = useState(INITIAL_ACCOUNTS);
  const [oauthOpen, setOauthOpen] = useState(false);
  const [brandTone, setBrandTone] = useState('Futuristic, authoritative, crisp, creator-first');
  const [brandPillars, setBrandPillars] = useState(['Local AI Workflows', 'Creator Automation', 'Privacy Architecture', 'Design Systems']);
  const addToast = useAppStore((s) => s.addToast);

  const handleRefreshToken = (id: string) => {
    setAccounts((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'connected' } : a)));
    addToast('OAuth Token Refreshed', 'Credentials encrypted and stored in local vault.', 'success');
  };

  const handleConnectPlatform = (platform: SocialAccount['platform']) => {
    setAccounts((prev) => [
      ...prev,
      {
        id: `acc-${Date.now()}`,
        platform,
        handle: `@javo_${platform.toLowerCase()}_new`,
        followers: 'New',
        status: 'connected',
        cadenceCap: '1 Post / day',
        brandVoice: 'Default Brand Voice',
      },
    ]);
    setOauthOpen(false);
    addToast(`${platform} Connected`, 'OAuth PKCE handshake completed cleanly.', 'success');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Social Accounts & Brand Profiles
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Encrypted OAuth tokens, Account Guardian (#11) rate limits, and Brand Manager (#06) tone profiles.
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setOauthOpen(true)}>
          Connect Account
        </Button>
      </div>

      {/* Connected Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {accounts.map((acc) => (
          <Card key={acc.id} variant="status" glow="cyan">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-11 w-11 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/10 flex items-center justify-center">
                  {platformIcon[acc.platform]}
                </div>
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                    {acc.handle}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {acc.platform} • {acc.followers} followers
                  </p>
                </div>
              </div>
              <Badge status={acc.status === 'connected' ? 'active' : 'warning'} size="sm">
                {acc.status === 'connected' ? 'OAuth Healthy' : 'Token Expiring'}
              </Badge>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <span className="text-slate-400">Safe Cadence Cap</span>
                <p className="mt-0.5 font-semibold text-slate-900 dark:text-white">{acc.cadenceCap}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10">
                <span className="text-slate-400">Brand Voice</span>
                <p className="mt-0.5 font-semibold text-slate-900 dark:text-white truncate">{acc.brandVoice}</p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between">
              <span className="inline-flex items-center gap-1 text-xs text-emerald-500">
                <ShieldCheck className="h-3.5 w-3.5" /> Guardian Protected
              </span>
              <Button
                size="sm"
                variant="secondary"
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                onClick={() => handleRefreshToken(acc.id)}
              >
                Refresh OAuth
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Brand Profile Card */}
      <Card variant="feature" glow="violet">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <Palette className="h-5 w-5 text-[#8B5CF6]" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Master Brand Profile
            </h2>
          </div>
          <Button
            size="sm"
            variant="violet"
            onClick={() =>
              addToast('Brand Profile Updated', 'Brand Manager (#06) synced updated voice rules.', 'success')
            }
          >
            Save Brand Rules
          </Button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">
              Global Tone & Voice Directive
            </label>
            <textarea
              rows={3}
              value={brandTone}
              onChange={(e) => setBrandTone(e.target.value)}
              className="w-full p-3 rounded-xl bg-white/80 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">
              Core Content Pillars
            </label>
            <div className="flex flex-wrap gap-2">
              {brandPillars.map((p) => (
                <Chip
                  key={p}
                  label={p}
                  variant="violet"
                  selected
                  removable
                  onRemove={() => setBrandPillars((prev) => prev.filter((item) => item !== p))}
                />
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* OAuth Flow Modal */}
      <Modal
        open={oauthOpen}
        onClose={() => setOauthOpen(false)}
        title="Connect Social Platform (PKCE OAuth)"
        description="Tokens are encrypted locally with AES-256-GCM and never leave your machine."
      >
        <div className="grid grid-cols-2 gap-3">
          {(['YouTube', 'Instagram', 'Facebook', 'X'] as const).map((platform) => (
            <button
              key={platform}
              type="button"
              onClick={() => handleConnectPlatform(platform)}
              className="flex items-center gap-3 p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 hover:border-[#00E5FF] transition-colors cursor-pointer"
            >
              {platformIcon[platform]}
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-900 dark:text-white">{platform}</p>
                <p className="text-xs text-slate-400">Authorize via OAuth 2.0</p>
              </div>
            </button>
          ))}
        </div>
      </Modal>
    </div>
  );
};
