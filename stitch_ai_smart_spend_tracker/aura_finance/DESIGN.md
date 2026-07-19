---
name: Aura Finance
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding-mobile: 16px
  container-padding-desktop: 32px
  gutter: 24px
  stack-sm: 4px
  stack-md: 12px
  stack-lg: 24px
---

## Brand & Style
The brand personality is rooted in "Financial Serenity"—a state where complex data becomes clear and actionable. This design system targets professionals and mindful spenders who value precision over flair. The emotional response should be one of quiet confidence, reliability, and growth.

The design style is **Fintech-Minimalist**. It draws heavily from **Corporate Modern** aesthetics but incorporates **Glassmorphism** and **Tonal Layering** to prevent the interface from feeling clinical. It prioritizes data density without clutter, using generous whitespace to reduce cognitive load during financial decision-making.

## Colors
The palette is engineered for professional trust and clear semantic signaling:
- **Primary (Deep Navy):** Used for primary navigation, headings, and high-importance UI elements to establish authority.
- **Secondary (Vibrant Emerald):** Reserved exclusively for "Growth" indicators, success states, and primary calls to action. This creates a psychological link between the color and positive financial movement.
- **Tertiary (Slate Gray):** Utilized for secondary information, icons, and supporting text to maintain a calm hierarchy.
- **Neutral (Ghost White/Slate):** The foundation for the "Tonal Layering" strategy, using varying shades of off-white and cool gray to separate surface areas.

## Typography
The system uses **Inter** for all UI and prose elements due to its exceptional legibility and neutral character. For specific financial data points, transaction IDs, and currency amounts in tables, **JetBrains Mono** is introduced as a secondary "data" font to ensure tabular numbers align perfectly and feel "technical."

Headlines use tighter letter-spacing and heavier weights to feel grounded. Body text maintains standard spacing for maximum readability in long-form transaction lists.

## Layout & Spacing
This design system utilizes a **Fixed Grid** model for desktop (1280px max-width) and a **Fluid Grid** for mobile devices. 

- **Desktop:** 12-column grid with 24px gutters. Sidebars are fixed at 280px.
- **Mobile:** 4-column fluid grid with 16px margins.
- **Rhythm:** An 8px linear scale governs all padding and margins. Use `stack-md` (12px) for internal card padding and `stack-lg` (24px) for spacing between major sections.

## Elevation & Depth
Depth is communicated through **Ambient Shadows** and **Tonal Layers** rather than heavy borders.

- **Level 0 (Background):** Slate-50 (#F8FAFC).
- **Level 1 (Cards/Surface):** Pure White (#FFFFFF) with a 1px border in Slate-200.
- **Level 2 (Dropdowns/Modals):** Pure White with a "Deep Ambient" shadow: `0px 12px 24px -4px rgba(15, 23, 42, 0.08)`.
- **Glass Effect:** Use a subtle backdrop blur (12px) with 80% opacity on global navigation headers to maintain a sense of space as the user scrolls.

## Shapes
The shape language is "Soft-Professional." A standard radius of **12px** is applied to most UI components (cards, input fields, buttons). For larger containers like dashboard widgets, use a **16px** (`rounded-lg`) radius. This softens the mathematical nature of financial data, making the application feel more approachable and modern.

## Components
- **Buttons:** Primary buttons use the Primary Deep Navy with white text. "Growth" buttons (e.g., "Add Funds") use the Secondary Emerald. All buttons have a 12px corner radius and a subtle 2px vertical inner-shadow on hover.
- **Input Fields:** Use a Slate-100 background with a 1px Slate-200 border. On focus, the border transitions to Primary Navy with a soft 4px outer glow.
- **Cards:** White background, 16px padding, 12px radius. Use "Tonal Headers" (a light gray subtle bar at the top) to distinguish widget types.
- **Chips/Status:** Rounded-full (pill-shaped). "Income" uses Emerald with 10% opacity background; "Expense" uses a soft Rose-red with 10% opacity.
- **Financial Lists:** High-density rows with 1px Slate-50 dividers. Use `data-mono` typography for currency values to ensure decimal points align vertically across rows.
- **Smart Widgets:** Dynamic charts should use the Emerald color for positive trends and Slate-400 for neutral/historical data, avoiding traditional "Warning" colors unless a critical budget threshold is exceeded.