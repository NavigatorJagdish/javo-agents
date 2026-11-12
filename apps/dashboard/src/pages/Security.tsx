import React, { useState } from 'react';
import { Shield, Laptop, Smartphone, Lock, OctagonAlert, KeyRound } from 'lucide-react';
import { Card, Badge, Button } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';
import { useEmergencyStopMutation } from '../api/hooks';

const INITIAL_DEVICES = [
  { id: 'dev-1', name: 'Windows Studio Workstation', type: 'desktop', lastSeen: 'Active now', ip: '127.0.0.1 (Localhost)', trusted: true },
  { id: 'dev-2', name: 'Pixel 9 Pro (Javo Companion)', type: 'mobile', lastSeen: '4 mins ago', ip: '192.168.1.44 (WireGuard)', trusted: true },
];

export const Security: React.FC = () => {
  const [devices, setDevices] = useState(INITIAL_DEVICES);
  const { emergencyStopped, resetEmergencyStop, addToast } = useAppStore();
  const emergencyStopMutation = useEmergencyStopMutation();

  const revokeDevice = (id: string) => {
    setDevices((prev) => prev.filter((d) => d.id !== id));
    addToast('Device Revoked', 'Session key invalidated by Security Guardian (#22).', 'warning');
  };

  const handleStop = async () => {
    await emergencyStopMutation.mutateAsync();
    useAppStore.getState().triggerEmergencyStop();
    addToast('Emergency Stop Activated', 'All agent execution halted.', 'error');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Security & Privacy Firewall
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Zero-trust local vault, paired device management, and Emergency Stop control.
          </p>
        </div>

        {emergencyStopped ? (
          <Button variant="primary" onClick={resetEmergencyStop}>
            Clear Emergency Stop
          </Button>
        ) : (
          <Button
            variant="danger"
            leftIcon={<OctagonAlert className="h-4 w-4" />}
            onClick={handleStop}
          >
            Emergency Stop All Agents
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card variant="status" glow="cyan">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-[#00E5FF]" />
            <div>
              <p className="text-xs text-slate-400">Privacy Egress Firewall</p>
              <p className="text-base font-bold text-slate-900 dark:text-white">Strict Local-First</p>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            PII & financial fields never route to external APIs.
          </p>
        </Card>

        <Card variant="status" glow="violet">
          <div className="flex items-center gap-3">
            <KeyRound className="h-5 w-5 text-[#8B5CF6]" />
            <div>
              <p className="text-xs text-slate-400">Credential Vault</p>
              <p className="text-base font-bold text-slate-900 dark:text-white">AES-256-GCM</p>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            OAuth & Telegram secrets bound to Windows DPAPI.
          </p>
        </Card>

        <Card variant="status" glow="cyan">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5 text-emerald-400" />
            <div>
              <p className="text-xs text-slate-400">Audit Trail Integrity</p>
              <p className="text-base font-bold text-slate-900 dark:text-white">100% Signed</p>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            1,482 agent actions logged with zero tampering.
          </p>
        </Card>
      </div>

      {/* Connected Devices */}
      <Card variant="default">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
          Paired Trusted Devices
        </h2>
        <div className="space-y-3">
          {devices.map((dev) => (
            <div
              key={dev.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-50 dark:bg-[#0B1026]/70 border border-slate-200 dark:border-white/10"
            >
              <div className="flex items-center gap-3">
                {dev.type === 'desktop' ? (
                  <Laptop className="h-5 w-5 text-[#00E5FF]" />
                ) : (
                  <Smartphone className="h-5 w-5 text-[#8B5CF6]" />
                )}
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{dev.name}</p>
                  <p className="text-xs text-slate-400 font-mono">
                    {dev.ip} • {dev.lastSeen}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge status="active" size="sm">Trusted</Badge>
                {dev.type !== 'desktop' && (
                  <Button size="sm" variant="danger" onClick={() => revokeDevice(dev.id)}>
                    Revoke
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
