# Javo Agents Brand Guidelines

## 1. Brand Identity & Symbolism

The **Javo Agents** mark unifies four visual elements representing a private, autonomous multi-agent team:

1. **Hexagonal Shield**: Local-first security, cryptographic boundaries, and supervised autopilot safety.
2. **Connected 3-Node Graph**: Multi-agent orchestration across Windows Desktop, Android Companion, and Social Connectors.
3. **5-Bar Vertical Equalizer / Waveform**: Voice-first command interface (`Listening`, `Thinking`, `Executing`, `Finished`).
4. **Tilted Orbital Ring**: Continuous 24/7 background scheduling and cross-device sync.

---

## 2. Color System

### Core Brand Colors (Dark Signature Mode)
| Token | Hex | Usage |
| :--- | :--- | :--- |
| `bg-midnight-navy` | `#0B1026` | Primary application canvas & splash background |
| `surface-deep-indigo` | `#111938` | Elevated cards, sidebar, modal surfaces |
| `border-slate-glow` | `#1E294D` | Hairline card borders and dividers |
| `accent-electric-cyan` | `#00E5FF` | Primary CTAs, active nav states, waveform peaks |
| `accent-violet` | `#8B5CF6` | Secondary badges, AI tags, gradient end-stop |
| `text-white` | `#FFFFFF` | Headings and primary metrics |
| `text-soft-silver` | `#E2E6F0` | Body copy and secondary labels |

### Light Mode Equivalents
| Token | Hex | Usage |
| :--- | :--- | :--- |
| `bg-ice-canvas` | `#F8FAFC` | Light canvas background |
| `surface-pure` | `#FFFFFF` | Elevated cards |
| `accent-cyan-deep` | `#00B4D8` | High-contrast cyan on light backgrounds |
| `accent-violet-deep` | `#7C3AED` | High-contrast violet on light backgrounds |
| `text-navy` | `#0B1026` | Primary text on light backgrounds |

### Semantic Status Palette
- **Success / Active**: `#10B981`
- **Warning / Approval Pending**: `#F59E0B`
- **Error / Emergency Stop**: `#EF4444`
- **Info / Local Processing**: `#38BDF8`

---

## 3. Logo Variants & Usage Rules

| File | Variant | Intended Context |
| :--- | :--- | :--- |
| `logos/javo-logo-primary.svg` | Full lockup (Dark) | Desktop header, marketing dark hero, docs |
| `logos/javo-logo-light.svg` | Full lockup (Light) | Light theme docs, whitepapers, print |
| `logos/javo-logo-mark.svg` | Shield mark only | App headers, collapsed sidebar, badges |
| `logos/javo-logo-mono.svg` | Monochrome (`currentColor`) | Watermarks, monochrome icons, print stamps |
| `icons/favicon.svg` | 64x64 browser icon | Web dashboard & website favicon |
| `icons/windows-app-icon.svg` | 256x256 app tile | Windows `.exe` / NSIS installer & Start Menu |
| `splash/splash-dark.svg` | 1280x720 splash | Electron startup & Android dark splash |
| `splash/splash-light.svg` | 1280x720 splash | Light mode startup |

### Clearspace & Minimum Size
- Maintain clearspace around the mark equal to at least **25% of the shield height** (`0.25H`) on all sides.
- Minimum digital width: `24px` for `javo-logo-mark.svg`, `140px` for horizontal wordmark lockups.
- **Do not** stretch, skew, remove the orbital ring on full-color marks, or place Electric Cyan text directly over `#FFFFFF` without darkening to `#00B4D8`.

---

## 4. Typography

- **Primary UI & Display Font**: `Inter`, fallback `'Segoe UI', system-ui, -apple-system, sans-serif`
- **Monospace / Code & Logs**: `'JetBrains Mono', 'Cascadia Code', Consolas, monospace`
- **Type Scale**:
  - Display Hero: `36px–48px`, `800` weight, `-0.02em` tracking
  - Page Title (`H1`): `24px–28px`, `700` weight
  - Section Header (`H2`): `18px–20px`, `600` weight
  - Body: `14px`, `400` weight, `1.5` line-height
  - Caption / Chip: `11px–12px`, `600` weight, uppercase tracking `0.06em`

---

## 5. Spacing & Elevation

- Base grid unit: `4px` (`4, 8, 12, 16, 20, 24, 32, 48, 64`).
- Standard card radius: `16px`; button/chip radius: `10px` / `9999px` (pill).
- Glow elevation (Dark mode): `0 0 24px rgba(0, 229, 255, 0.14)` for active AI cards and waveform containers.

---

## 6. Generating Windows `.ico` and `.png` Assets

Run the included script from `packages/brand-assets/icons/`:

```powershell
python generate_icons.py
```

Outputs are written to `packages/brand-assets/icons/dist/` (`javo-app.ico`, `tray-icon.png`, and `javo-icon-{16..256}.png`).
