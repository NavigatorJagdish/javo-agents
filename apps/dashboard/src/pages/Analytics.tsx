import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { TrendingUp, Eye, Users, MousePointerClick } from 'lucide-react';
import { Card, MetricCard, Chip } from '@javo/design-system';

const weeklyViews = [
  { date: 'Nov 06', youtube: 14200, instagram: 9800, x: 4300 },
  { date: 'Nov 07', youtube: 16900, instagram: 11200, x: 5100 },
  { date: 'Nov 08', youtube: 15400, instagram: 13400, x: 4800 },
  { date: 'Nov 09', youtube: 21300, instagram: 14900, x: 6200 },
  { date: 'Nov 10', youtube: 24800, instagram: 17100, x: 7400 },
  { date: 'Nov 11', youtube: 22100, instagram: 16500, x: 6900 },
  { date: 'Nov 12', youtube: 28900, instagram: 19800, x: 8500 },
];

const platformCompare = [
  { platform: 'YouTube', engagement: 8.4, retention: 71 },
  { platform: 'Instagram', engagement: 6.9, retention: 64 },
  { platform: 'X', engagement: 4.8, retention: 52 },
  { platform: 'Facebook', engagement: 3.9, retention: 48 },
];

export const Analytics: React.FC = () => {
  const [range, setRange] = useState<'7d' | '30d' | '90d'>('7d');
  const multiplier = range === '7d' ? 1 : range === '30d' ? 4.1 : 11.8;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Cross-Platform Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Performance telemetry compiled by Weekly Analyst (#19) & Growth Scientist (#01).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {(['7d', '30d', '90d'] as const).map((r) => (
            <Chip
              key={r}
              label={r.toUpperCase()}
              selected={range === r}
              onClick={() => setRange(r)}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          title="Total Impressions"
          value={`${Math.round(289 * multiplier)}K`}
          trend="+24.2%"
          subtitle={`last ${range}`}
          accent="cyan"
          icon={<Eye className="h-5 w-5" />}
        />
        <MetricCard
          title="Net New Followers"
          value={`+${Math.round(3420 * multiplier).toLocaleString()}`}
          trend="+16.8%"
          subtitle="across 4 channels"
          accent="violet"
          icon={<Users className="h-5 w-5" />}
        />
        <MetricCard
          title="Avg Engagement Rate"
          value="7.1%"
          trend="+1.3%"
          subtitle="hook-tested posts"
          accent="emerald"
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <MetricCard
          title="Link Clicks"
          value={Math.round(6840 * multiplier).toLocaleString()}
          trend="+11.4%"
          subtitle="UTM attributed"
          accent="cyan"
          icon={<MousePointerClick className="h-5 w-5" />}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card variant="default">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
            Daily Views by Platform
          </h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyViews}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={12} />
                <YAxis stroke="#94A3B8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F1736',
                    borderColor: 'rgba(0,229,255,0.3)',
                    borderRadius: '12px',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="youtube" name="YouTube" stroke="#00E5FF" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="instagram" name="Instagram" stroke="#8B5CF6" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="x" name="X" stroke="#10B981" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card variant="default">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
            Platform Retention vs Engagement (%)
          </h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={platformCompare}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis dataKey="platform" stroke="#94A3B8" fontSize={12} />
                <YAxis stroke="#94A3B8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F1736',
                    borderColor: 'rgba(139,92,246,0.35)',
                    borderRadius: '12px',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Bar dataKey="retention" name="Avg Retention %" fill="#00E5FF" radius={[8, 8, 0, 0]} />
                <Bar dataKey="engagement" name="Engagement %" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
};
