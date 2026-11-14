import React, { lazy } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { OwnerAccess } from './components/OwnerAccess';
import { MainLayout } from './layouts/MainLayout';
import { AuthLayout } from './layouts/AuthLayout';

const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const AITeam = lazy(() => import('./pages/AITeam').then(module => ({ default: module.AITeam })));
const Goals = lazy(() => import('./pages/Goals').then(module => ({ default: module.Goals })));
const Content = lazy(() => import('./pages/Content').then(module => ({ default: module.Content })));
const Workflows = lazy(() => import('./pages/Workflows').then(module => ({ default: module.Workflows })));
const Automation = lazy(() => import('./pages/Automation').then(module => ({ default: module.Automation })));
const Accounts = lazy(() => import('./pages/Accounts').then(module => ({ default: module.Accounts })));
const Integrations = lazy(() => import('./pages/Integrations').then(module => ({ default: module.Integrations })));
const Analytics = lazy(() => import('./pages/Analytics').then(module => ({ default: module.Analytics })));
const Approvals = lazy(() => import('./pages/Approvals').then(module => ({ default: module.Approvals })));
const Voice = lazy(() => import('./pages/Voice').then(module => ({ default: module.Voice })));
const GitHub = lazy(() => import('./pages/GitHub').then(module => ({ default: module.GitHub })));
const Skills = lazy(() => import('./pages/Skills').then(module => ({ default: module.Skills })));
const Security = lazy(() => import('./pages/Security').then(module => ({ default: module.Security })));
const Settings = lazy(() => import('./pages/Settings').then(module => ({ default: module.Settings })));

const Welcome = lazy(() => import('./pages/setup/Welcome').then(module => ({ default: module.Welcome })));
const HardwareCheck = lazy(() => import('./pages/setup/HardwareCheck').then(module => ({ default: module.HardwareCheck })));
const AISetup = lazy(() => import('./pages/setup/AISetup').then(module => ({ default: module.AISetup })));
const ContentFolder = lazy(() => import('./pages/setup/ContentFolder').then(module => ({ default: module.ContentFolder })));
const SocialAccounts = lazy(() => import('./pages/setup/SocialAccounts').then(module => ({ default: module.SocialAccounts })));
const BrandSetup = lazy(() => import('./pages/setup/BrandSetup').then(module => ({ default: module.BrandSetup })));
const AutopilotConfig = lazy(() => import('./pages/setup/AutopilotConfig').then(module => ({ default: module.AutopilotConfig })));
const TelegramSetup = lazy(() => import('./pages/setup/TelegramSetup').then(module => ({ default: module.TelegramSetup })));
const VoiceSetup = lazy(() => import('./pages/setup/VoiceSetup').then(module => ({ default: module.VoiceSetup })));
const PrivacyControls = lazy(() => import('./pages/setup/PrivacyControls').then(module => ({ default: module.PrivacyControls })));
const Diagnostics = lazy(() => import('./pages/setup/Diagnostics').then(module => ({ default: module.Diagnostics })));
const Complete = lazy(() => import('./pages/setup/Complete').then(module => ({ default: module.Complete })));

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
      <OwnerAccess>
      <HashRouter>
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
      </HashRouter>
      </OwnerAccess>
    </QueryClientProvider>
  );
}

export default App;
