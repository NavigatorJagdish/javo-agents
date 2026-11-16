import React from 'react';
import { MessageCircle } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const TelegramSetup: React.FC = () => <SetupStepCard title="Telegram bridge availability" subtitle="Secure paired Telegram commands are not ready in this build." icon={<MessageCircle className="h-6 w-6" />} prevPath="/setup/autopilot" nextPath="/setup/voice">
  <p className="text-sm">Bot registration, owner pairing, replay protection, scoped commands and approval verification still need integration. No Telegram connection is created by this guide.</p>
  <p className="text-sm text-slate-500">Use the local dashboard for supported actions. Do not enter bot tokens into prototype screens; this step does not collect or save them.</p>
</SetupStepCard>;
