import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { MainLayout } from './layouts/MainLayout';
import { AuthLayout } from './layouts/AuthLayout';

import { Dashboard } from './pages/Dashboard';
import { AITeam } from './pages/AITeam';
import { Goals } from './pages/Goals';
import { Content } from './pages/Content';
import { Workflows } from './pages/Workflows';
import { Automation } from './pages/Automation';
import { Accounts } from './pages/Accounts';
import { Integrations } from './pages/Integrations';
import { Analytics } from './pages/Analytics';
import { Approvals } from './pages/Approvals';
import { Voice } from './pages/Voice';
import { GitHub } from './pages/GitHub';
import { Skills } from './pages/Skills';
import { Security } from './pages/Security';
import { Settings } from './pages/Settings';

import { Welcome } from './pages/setup/Welcome';
import { HardwareCheck } from './pages/setup/HardwareCheck';
import { AISetup } from './pages/setup/AISetup';
import { ContentFolder } from './pages/setup/ContentFolder';
import { SocialAccounts } from './pages/setup/SocialAccounts';
import { BrandSetup } from './pages/setup/BrandSetup';
import { AutopilotConfig } from './pages/setup/AutopilotConfig';
import { TelegramSetup } from './pages/setup/TelegramSetup';
import { VoiceSetup } from './pages/setup/VoiceSetup';
import { PrivacyControls } from './pages/setup/PrivacyControls';
import { Diagnostics } from './pages/setup/Diagnostics';
import { Complete } from './pages/setup/Complete';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ai-team" element={<AITeam />} />
            <Route path="/goals" element={<Goals />} />
            <Route path="/content" element={<Content />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/automation" element={<Automation />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/voice" element={<Voice />} />
            <Route path="/github" element={<GitHub />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/security" element={<Security />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          <Route path="/setup" element={<AuthLayout />}>
            <Route index element={<Navigate to="/setup/welcome" replace />} />
            <Route path="welcome" element={<Welcome />} />
            <Route path="hardware" element={<HardwareCheck />} />
            <Route path="ai" element={<AISetup />} />
            <Route path="folder" element={<ContentFolder />} />
            <Route path="social" element={<SocialAccounts />} />
            <Route path="brand" element={<BrandSetup />} />
            <Route path="autopilot" element={<AutopilotConfig />} />
            <Route path="telegram" element={<TelegramSetup />} />
            <Route path="voice" element={<VoiceSetup />} />
            <Route path="privacy" element={<PrivacyControls />} />
            <Route path="diagnostics" element={<Diagnostics />} />
            <Route path="complete" element={<Complete />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
