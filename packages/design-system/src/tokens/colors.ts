export const colors = {
  brand: {
    midnightNavy: '#0B1026',
    deepSpace: '#0F1736',
    cardSurface: '#131C40',
    elevatedSurface: '#1A2552',
    electricCyan: '#00E5FF',
    cyanHover: '#33ECFF',
    cyanDim: 'rgba(0, 229, 255, 0.14)',
    violetAccent: '#8B5CF6',
    violetHover: '#A78BFA',
    violetDim: 'rgba(139, 92, 246, 0.16)',
  },
  neutral: {
    white: '#FFFFFF',
    softSilver: '#E2E6F0',
    mutedSilver: '#94A3B8',
    slateBorder: 'rgba(226, 230, 240, 0.12)',
    lightBg: '#F4F7FB',
    lightSurface: '#FFFFFF',
    lightText: '#0F172A',
    lightMuted: '#475569',
    lightBorder: '#E2E8F0',
  },
  semantic: {
    success: '#10B981',
    successDim: 'rgba(16, 185, 129, 0.15)',
    warning: '#F59E0B',
    warningDim: 'rgba(245, 158, 11, 0.15)',
    error: '#EF4444',
    errorDim: 'rgba(239, 68, 68, 0.15)',
    info: '#38BDF8',
    infoDim: 'rgba(56, 189, 248, 0.15)',
  },
  gradients: {
    cyanPrimary: 'linear-gradient(135deg, #00E5FF 0%, #0EA5E9 100%)',
    cyanViolet: 'linear-gradient(135deg, #00E5FF 0%, #8B5CF6 100%)',
    navyCard: 'linear-gradient(160deg, rgba(26, 37, 82, 0.85) 0%, rgba(15, 23, 54, 0.95) 100%)',
    glowCyan: '0 0 24px rgba(0, 229, 255, 0.25)',
    glowViolet: '0 0 24px rgba(139, 92, 246, 0.28)',
  },
} as const;

export type ColorTokens = typeof colors;
