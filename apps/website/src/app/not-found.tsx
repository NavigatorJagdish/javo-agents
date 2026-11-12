import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { JavoLogo } from '@/components/JavoLogo';

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-2xl flex-col items-center justify-center px-4 text-center">
      <JavoLogo size={64} animated />
      <p className="mt-6 font-mono text-sm font-semibold text-[#007B8F] dark:text-[#00E5FF]">
        404 — ROUTE NOT FOUND
      </p>
      <h1 className="mt-2 font-display text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
        This page isn&apos;t in the local runtime
      </h1>
      <p className="mt-3 text-sm text-slate-600 dark:text-[#E2E6F0]/75">
        Check the URL or head back to the Javo Agents home page or documentation.
      </p>
      <div className="mt-6 flex gap-3">
        <Link href="/" className="btn-primary">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>
        <Link href="/docs" className="btn-secondary">
          Browse Docs
        </Link>
      </div>
    </div>
  );
}
