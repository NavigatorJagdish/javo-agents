import React, { useState } from 'react';
import {
  Cpu,
  Cloud,
  MessageCircle,
  Youtube,
  Instagram,
  Facebook,
  Github,
  Mic,
  Database,
  Webhook,
  FolderSync,
  Shield,
} from 'lucide-react';
import { FeatureCard, Badge, Button, Chip } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface IntegrationItem {
  id: string;
  name: string;
  category: 'AI Models' | 'Social' | 'Messaging' | 'Storage & Dev';
  description: string;
  connected: boolean;
  badge: string;
  icon: React.ReactNode;
}

const INITIAL_INTEGRATIONS: IntegrationItem[] = [
  { id: 'ollama', name: 'Ollama Local Runtime', category: 'AI Models', description: 'Run Qwen 2.5, Llama 3.2, and Nomic embeddings 100% offline on GPU/CPU.', connected: true, badge: 'Local First', icon: <Cpu className="h-5 w-5" /> },
  { id: 'gemini', name: 'Google Gemini API', category: 'AI Models', description: 'High-reasoning cloud fallback gated by Privacy Firewall & Budget Guardian.', connected: true, badge: 'Hybrid Cloud', icon: <Cloud className="h-5 w-5" /> },
  { id: 'telegram', name: 'Telegram Bot Bridge', category: 'Messaging', description: 'Approve posts, send voice notes, and run emergency stop from mobile.', connected: true, badge: 'Live Webhook', icon: <MessageCircle className="h-5 w-5" /> },
  { id: 'youtube', name: 'YouTube Data & Studio', category: 'Social', description: 'Upload Shorts/Videos, sync analytics velocity, and manage comment threads.', connected: true, badge: 'OAuth 2.0', icon: <Youtube className="h-5 w-5" /> },
  { id: 'instagram', name: 'Instagram Graph API', category: 'Social', description: 'Publish Reels & carousels, track saves, and moderate community DMs.', connected: true, badge: 'OAuth 2.0', icon: <Instagram className="h-5 w-5" /> },
  { id: 'facebook', name: 'Facebook Pages API', category: 'Social', description: 'Cross-post branded media and monitor engagement metrics.', connected: true, badge: 'OAuth 2.0', icon: <Facebook className="h-5 w-5" /> },
  { id: 'whisper', name: 'Whisper + Neural TTS', category: 'AI Models', description: 'Low-latency local speech recognition and voice response synthesis.', connected: true, badge: 'Audio Bus', icon: <Mic className="h-5 w-5" /> },
  { id: 'github', name: 'GitHub Skill Registry', category: 'Storage & Dev', description: 'Sync verified community skills and signed Windows desktop releases.', connected: true, badge: 'Signed', icon: <Github className="h-5 w-5" /> },
  { id: 'sqlite', name: 'Encrypted SQLite + Vector', category: 'Storage & Dev', description: 'Local-first WAL database with semantic Smart Memory recall.', connected: true, badge: 'AES-256', icon: <Database className="h-5 w-5" /> },
  { id: 'folder', name: 'Local Folder Watcher', category: 'Storage & Dev', description: 'Real-time file-system monitor for raw exports and render drops.', connected: true, badge: 'Watchdog', icon: <FolderSync className="h-5 w-5" /> },
  { id: 'webhooks', name: 'Custom REST Webhooks', category: 'Messaging', description: 'Trigger workflows from Zapier, n8n, OBS, or custom studio hardware.', connected: false, badge: 'Optional', icon: <Webhook className="h-5 w-5" /> },
  { id: 'firewall', name: 'Privacy Egress Firewall', category: 'Storage & Dev', description: 'Redacts PII and enforces strict local-only policy for sensitive assets.', connected: true, badge: 'Enforced', icon: <Shield className="h-5 w-5" /> },
];

export const Integrations: React.FC = () => {
  const [items, setItems] = useState(INITIAL_INTEGRATIONS);
  const [category, setCategory] = useState<string>('All');
  const addToast = useAppStore((s) => s.addToast);

  const toggleConnect = (id: string) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        const next = !item.connected;
        addToast(
          next ? `${item.name} Connected` : `${item.name} Disconnected`,
          next ? 'Connector verified and active.' : 'Connector disabled cleanly.',
          next ? 'success' : 'info'
        );
        return { ...item, connected: next };
      })
    );
  };

  const filtered = items.filter((i) => category === 'All' || i.category === category);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
          Integrations & Connectors
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Modular AI providers, social APIs, and local studio pipelines powered by API Integration (#08).
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {['All', 'AI Models', 'Social', 'Messaging', 'Storage & Dev'].map((cat) => (
          <Chip key={cat} label={cat} selected={category === cat} onClick={() => setCategory(cat)} />
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filtered.map((item) => (
          <FeatureCard
            key={item.id}
            title={item.name}
            description={item.description}
            icon={item.icon}
            badge={item.badge}
          >
            <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-white/10">
              <Badge status={item.connected ? 'active' : 'inactive'} size="sm" pulse={item.connected}>
                {item.connected ? 'Connected' : 'Disconnected'}
              </Badge>
              <Button
                size="sm"
                variant={item.connected ? 'secondary' : 'primary'}
                onClick={() => toggleConnect(item.id)}
              >
                {item.connected ? 'Configure' : 'Connect'}
              </Button>
            </div>
          </FeatureCard>
        ))}
      </div>
    </div>
  );
};
