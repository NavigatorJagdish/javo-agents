import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from '@/components/ThemeProvider';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: {
    default: `${SITE_CONFIG.name} — ${SITE_CONFIG.tagline}`,
    template: `%s | ${SITE_CONFIG.name}`,
  },
  description:
    'Local-first AI automation team for Windows and Android. Run 29 specialist agents on your own hardware with Supervised Autopilot, 8GB RAM optimization, Privacy Firewall, and Hindi/Hinglish/English Voice Mode.',
  icons: {
    icon: '/favicon.svg',
  },
  openGraph: {
    title: `${SITE_CONFIG.name} — ${SITE_CONFIG.tagline}`,
    description:
      'Local-first AI automation platform with 29 specialist agents, visual workflows, voice mode, and Supervised Autopilot. Initial v0.1.0-alpha release is $0/month (MIT).',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-[#F8FAFC] font-sans text-slate-900 antialiased dark:bg-[#0B1026] dark:text-white">
        <ThemeProvider>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
