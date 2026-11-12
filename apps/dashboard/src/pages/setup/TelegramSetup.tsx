import React, { useState } from 'react';
import { MessageCircle } from 'lucide-react';
import { SetupStepCard } from './SetupStepCard';

export const TelegramSetup: React.FC = () => {
  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');

  return (
    <SetupStepCard
      title="Telegram Mobile Bridge"
      subtitle="Receive instant approval cards, analytics digests, and voice control from Telegram."
      icon={<MessageCircle className="h-6 w-6" />}
      prevPath="/setup/autopilot"
      nextPath="/setup/voice"
    >
      <div>
        <label className="block text-xs font-medium mb-1">Bot Token (from @BotFather)</label>
        <input
          type="password"
          value={botToken}
          onChange={(e) => setBotToken(e.target.value)}
          placeholder="123456789:ABCdef..."
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1">Authorized Admin Chat ID</label>
        <input
          value={chatId}
          onChange={(e) => setChatId(e.target.value)}
          placeholder="e.g. 987654321"
          className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm font-mono"
        />
      </div>
    </SetupStepCard>
  );
};
