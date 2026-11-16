import React from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const ContentFolder: React.FC = () => <SetupStepCard title="Import local content" subtitle="Use Content to scan a real folder and review imported files." icon={<FolderOpen className="h-6 w-6" />} prevPath="/setup/ai" nextPath="/setup/social">
  <p className="text-sm">In Content, enter an existing local folder and select Scan folder. Review the saved assets, choose a destination, prepare a schedule and approve its exact preview before simulating dispatch.</p>
  <p className="text-sm text-slate-500">The original files are preserved. This guide does not configure an automatic publishing or archive-folder rule. Live publishing remains unavailable.</p>
  <Link to="/content" className="text-cyan-600 dark:text-cyan-300 underline">Open Content</Link>
</SetupStepCard>;
