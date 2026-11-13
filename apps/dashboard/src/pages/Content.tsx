import React, { useState } from 'react';
import {
  FolderSearch,
  Grid3X3,
  List,
  Video,
  Image as ImageIcon,
  FileText,
  Music,
  Layers,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { Card, Badge, Button, Chip, Modal } from '@javo/design-system';
import { useContentStore, type ContentItem, type ContentType } from '../store/useContentStore';
import { useAppStore } from '../store/useAppStore';

const typeIconMap: Record<ContentType, React.ReactNode> = {
  video: <Video className="h-5 w-5 text-[#00E5FF]" />,
  image: <ImageIcon className="h-5 w-5 text-[#8B5CF6]" />,
  carousel: <Layers className="h-5 w-5 text-sky-400" />,
  post: <FileText className="h-5 w-5 text-emerald-400" />,
  audio: <Music className="h-5 w-5 text-amber-400" />,
};

export const Content: React.FC = () => {
  const { assets, updateStatus } = useContentStore();
  const addToast = useAppStore((s) => s.addToast);

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterType, setFilterType] = useState<string>('all');
  const [previewItem, setPreviewItem] = useState<ContentItem | null>(null);
  const [scheduleDate, setScheduleDate] = useState('2026-11-15T18:00');

  const filtered = assets.filter((a) => filterType === 'all' || a.type === filterType);

  const handleScanFolder = () => {
    addToast('Folder Watcher Sync', 'Scanned D:/CreatorContent — 0 unindexed files remaining.', 'success');
  };

  const handleSchedule = () => {
    if (!previewItem) return;
    updateStatus(previewItem.id, 'scheduled', scheduleDate.replace('T', ' '));
    addToast('Asset Scheduled', `"${previewItem.title}" scheduled for ${previewItem.platform}.`, 'success');
    setPreviewItem(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Content Library
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Watched local folders, AI quality scores, metadata tags, and multi-platform scheduling.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="secondary" leftIcon={<FolderSearch className="h-4 w-4" />} onClick={handleScanFolder}>
            Scan Folder
          </Button>
          <div className="inline-flex rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#131C40] p-1">
            <button
              type="button"
              aria-label="Grid view"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg cursor-pointer ${
                viewMode === 'grid' ? 'bg-[#00E5FF]/20 text-[#00E5FF]' : 'text-slate-400'
              }`}
            >
              <Grid3X3 className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="List view"
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg cursor-pointer ${
                viewMode === 'list' ? 'bg-[#00E5FF]/20 text-[#00E5FF]' : 'text-slate-400'
              }`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {['all', 'video', 'carousel', 'image', 'post', 'audio'].map((t) => (
          <Chip
            key={t}
            label={t === 'all' ? 'All Assets' : t.toUpperCase()}
            selected={filterType === t}
            onClick={() => setFilterType(t)}
          />
        ))}
      </div>

      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((item) => (
            <Card
              key={item.id}
              variant="status"
              glow="cyan"
              interactive
              onClick={() => setPreviewItem(item)}
              className="flex flex-col justify-between"
            >
              <div>
                <div className="h-36 rounded-xl bg-gradient-to-br from-[#0F1736] to-[#1A2552] border border-white/10 flex flex-col items-center justify-center relative overflow-hidden">
                  {typeIconMap[item.type]}
                  <span className="mt-2 text-xs font-mono text-slate-300 uppercase">
                    {item.type} {item.duration ? `• ${item.duration}` : `• ${item.size}`}
                  </span>
                  <div className="absolute top-2.5 right-2.5">
                    <Badge
                      status={
                        item.status === 'published'
                          ? 'active'
                          : item.status === 'simulated'
                            ? 'violet'
                            : item.status === 'scheduled'
                              ? 'info'
                              : item.status === 'ready'
                                ? 'violet'
                                : 'warning'
                      }
                      size="sm"
                    >
                      {item.status === 'published'
                        ? 'Live Published'
                        : item.status === 'simulated'
                          ? 'Simulated (Mock)'
                          : item.status}
                    </Badge>
                  </div>
                  <div className="absolute bottom-2.5 left-2.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-black/50 text-[11px] text-[#00E5FF]">
                    <Sparkles className="h-3 w-3" /> QA {item.aiScore}/100
                  </div>
                </div>

                <h3 className="mt-4 text-sm font-semibold text-slate-900 dark:text-white line-clamp-1">
                  {item.title}
                </h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                  {item.caption}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200 dark:border-white/10 flex items-center justify-between text-xs">
                <span className="font-medium text-[#7C3AED] dark:text-[#A78BFA]">{item.platform}</span>
                <span className="text-slate-400 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {item.scheduledAt ?? item.createdAt}
                </span>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card variant="default" padding="none" className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 dark:border-white/10 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Asset</th>
                <th className="px-4 py-3">Platform</th>
                <th className="px-4 py-3">QA Score</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Schedule / Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-white/10">
              {filtered.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setPreviewItem(item)}
                  className="hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {typeIconMap[item.type]}
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{item.title}</p>
                        <p className="text-xs text-slate-400 font-mono">{item.folder}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs font-medium">{item.platform}</td>
                  <td className="px-4 py-3 font-mono text-xs text-[#008CA8] dark:text-[#00E5FF]">
                    {item.aiScore}/100
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      status={
                        item.status === 'published'
                          ? 'active'
                          : item.status === 'simulated'
                            ? 'violet'
                            : 'info'
                      }
                      size="sm"
                    >
                      {item.status === 'published'
                        ? 'Live Published'
                        : item.status === 'simulated'
                          ? 'Simulated (Mock)'
                          : item.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">
                    {item.scheduledAt ?? item.createdAt}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* File Preview & Schedule Modal */}
      <Modal
        open={Boolean(previewItem)}
        onClose={() => setPreviewItem(null)}
        title={previewItem?.title}
        description={previewItem ? `${previewItem.platform} • ${previewItem.folder}` : ''}
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={() => setPreviewItem(null)}>
              Close
            </Button>
            <Button variant="primary" onClick={handleSchedule}>
              Save Schedule
            </Button>
          </>
        }
      >
        {previewItem && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/10">
              <p className="text-xs font-semibold uppercase text-slate-400 mb-1">AI Caption</p>
              <p className="text-sm">{previewItem.caption}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {previewItem.tags.map((tag) => (
                <Chip key={tag} label={`#${tag}`} variant="violet" selected />
              ))}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium mb-1">Publish Date & Time</label>
                <input
                  type="datetime-local"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
                />
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-400">Quality Inspector Score</p>
                <p className="text-lg font-bold font-mono text-[#008CA8] dark:text-[#00E5FF]">
                  {previewItem.aiScore} / 100
                </p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
