import React, { useState } from 'react';
import { FolderOpen } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const ContentFolder: React.FC = () => {
  const [watchPath, setWatchPath] = useState('D:\\CreatorContent\\Ready');
  const [archivePath, setArchivePath] = useState('D:\\CreatorContent\\Published');

  return (
    <SetupStepCard
      title="Content Watch Folders"
      subtitle="Folder Watcher triggers workflows automatically whenever you drop new exports."
      icon={<FolderOpen className="h-6 w-6" />}
      prevPath="/setup/ai"
      nextPath="/setup/social"
    >
      <div>
        <label className="block text-xs font-medium mb-1">Primary Drop Folder</label>
        <input
          value={watchPath}
          onChange={(e) => setWatchPath(e.target.value)}
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1">Published Archive Folder</label>
        <input
          value={archivePath}
          onChange={(e) => setArchivePath(e.target.value)}
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
        />
      </div>
    </SetupStepCard>
  );
};
