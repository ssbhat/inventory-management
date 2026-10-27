---
name: saas-ui-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical sidebar navigation on the left (replacing a top nav bar), a consistent spacing scale, design tokens, and a polished professional look. Use when asked to modernize, restyle, or redesign a Vue 3 app's layout or navigation, add a sidebar, or make the UI look like a SaaS dashboard.
---

# SaaS UI Redesign for Vue 3

Turn an existing Vue 3 app into a clean SaaS-style interface. The app gets a fixed left sidebar, a slim top bar inside the content area, and one shared set of design tokens that every view uses.

This is a **visual and layout** change. Routes, API calls, data logic, i18n keys and component behavior must work exactly as before.

## Target layout

```
┌────────────┬──────────────────────────────────────────────┐
│  Logo      │  Top bar: page title · filters · profile     │
│            ├──────────────────────────────────────────────┤
│  ▸ Nav     │                                              │
│  ▸ Nav     │   Page header (title, description, actions)  │
│  ▸ Nav     │   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│            │   │ KPI  │ │ KPI  │ │ KPI  │ │ KPI  │       │
│  ── group  │   └──────┘ └──────┘ └──────┘ └──────┘       │
│  ▸ Nav     │   ┌──────────────────────────────────┐      │
│            │   │ Card / table / chart             │      │
│  ─────     │   └──────────────────────────────────┘      │
│  « Collapse│                                              │
└────────────┴──────────────────────────────────────────────┘
 240px (64px collapsed)    content: max-width 1440px, centered
```

- Below 1024px the sidebar starts collapsed to icons.
- Below 768px it becomes an off-canvas drawer, opened by a menu button in the top bar, with a backdrop.

## Workflow

Do the steps in order, and confirm each one works before starting the next.

### 1. Audit the current app (read-only)
Find and note:
- **App shell:** usually `src/App.vue`. Look for the top nav, header widgets (language switcher, profile menu, filter bar) and `<router-view>`.
- **Routes:** `src/main.js` or `src/router/*`. List every path, plus the nav label and translation key for each.
- **Global styles:** `<style>` without `scoped` in `App.vue`, `src/assets/*.css` or `src/style.css`. Record the existing colors, fonts and shared class names (`.card`, `.badge`, `.stat-card`, `.page-header`, tables).
- **Views and components:** `src/views/*.vue` and `src/components/*.vue`. Note one-off spacing values, hard-coded colors and duplicated styles.
- **Project rules:** CLAUDE.md files and `.claude/agents/`. If the project says `.vue` work must go to a specific agent (for example `vue-expert`), send each `.vue` edit there and give it this skill's rules.
- **Dependencies:** `package.json`. Use an icon or UI library only if one is already installed. Otherwise use inline SVG and plain CSS, and **add no new dependencies** unless the user agrees.

Then tell the user in a few lines what will change, and ask about anything the code can't settle, such as brand color or nav grouping.

### 2. Add design tokens
Create `src/styles/tokens.css` from [references/tokens.css](references/tokens.css) and import it once in `main.js`, before the app mounts.
- Carry the app's existing brand colors into the token values. Don't silently swap brand colors.
- From here on, every spacing, color, radius, shadow and font size uses a `var(--…)` token. Don't use raw hex values or one-off pixel values in components.

### 3. Build the app shell
Follow [references/app-shell.md](references/app-shell.md):
- `src/components/layout/AppSidebar.vue`: logo, grouped nav built from a single `navItems` array, active state from the router, collapse toggle, mobile drawer.
- `src/components/layout/AppTopbar.vue`: menu button (mobile), current page title, and the existing header widgets (filters, language switcher, profile) moved here **unchanged**.
- `App.vue` becomes a CSS grid shell: sidebar, then top bar plus `<main>`. Delete the old top-nav markup and its CSS.
- Remember the collapsed state in `localStorage`, wrapped in try/catch.

### 4. Restyle shared patterns globally
Update the global (unscoped) styles so every view benefits at once:
- **Page header:** title (`--text-2xl`, semibold), muted description, actions aligned right.
- **Cards:** `--surface` background, 1px `--border`, `--radius-lg`, `--shadow-sm`, `--space-6` padding, and a header row with title and actions.
- **KPI / stat cards:** label (`--text-sm`, muted), value (`--text-3xl`, semibold, tabular numbers), optional change indicator. Lay them out in a responsive grid: `repeat(auto-fit, minmax(220px, 1fr))`.
- **Tables:** sticky header, `--text-sm`, roomy rows (`--space-3` vertical padding), row hover with `--surface-hover`, numbers right-aligned with `font-variant-numeric: tabular-nums`, and the table wrapped in an `overflow-x: auto` container.
- **Badges:** pill shape, soft tinted background with strong text, mapped to success / info / warning / danger tokens.
- **Buttons and inputs:** primary, secondary and ghost buttons. 36px height, `--radius-md`, and a visible `:focus-visible` ring.
- **States:** loading skeletons or spinners, error and empty states, all styled the same way.

### 5. Clean up each view
Go through the views one at a time:
- Swap hard-coded colors and spacing for tokens.
- Remove scoped CSS that duplicates the new global patterns.
- Use the 8-point scale for gaps between sections: `--space-6` between cards and `--space-8` between major sections.
- Leave template logic, `v-for` keys, computed properties and API calls alone.

### 6. Verify
- **Build:** `npm run build` must pass with no new warnings.
- **Visual check:** run the app and, if Playwright or a browser tool is available, screenshot every route at 1440px, 1024px and 390px. Check:
  - sidebar active state is correct on every route
  - collapse works, and survives a reload
  - mobile drawer opens and closes, and Esc and the backdrop both close it
  - no horizontal page scroll at 390px
  - text stays readable with the longest translation, if there's a second language
  - focus rings are visible when tabbing through the sidebar
- **Behavior:** filters, modals, forms and language switching all still work.
- **Report:** tell the user what changed, with before and after screenshots if you took them.

## Design rules

- **Spacing:** use only the 4px-based scale in the tokens file. Content area padding: `--space-8` on desktop, `--space-4` on mobile.
- **Typography:** use the system font stack, or the app's existing font. Use three weights at most (400, 500, 600). Body text is `--text-sm` or `--text-base`, with line height 1.5.
- **Color:** keep the UI neutral, slate or gray. Use the brand accent sparingly: active nav item, primary buttons, links and focus rings. Status colors are only for status.
- **Depth:** prefer borders to shadows. Use `--shadow-sm` on cards and `--shadow-lg` only on popovers, modals and the mobile drawer.
- **Icons:** 18–20px, 1.5–2px stroke, `currentColor`, with one icon per nav item. When the sidebar is collapsed, show the label as a `title` tooltip and keep it as an `aria-label`.
- **Motion:** use 150–200ms ease transitions for sidebar width, hover and drawer, and respect `prefers-reduced-motion`.
- **Accessibility:**
  - The sidebar is a `<nav aria-label="Main">` and the active link has `aria-current="page"`.
  - The collapse toggle uses `aria-expanded`.
  - Text meets AA contrast, at least 4.5:1.
  - Click targets are at least 36px.
- **Dark mode:** only add it if the user asks. The tokens are structured so you can add it later by overriding them under `[data-theme="dark"]`.
- **No emojis** in the UI.

## Things not to do

- Don't change routes, route paths, API calls, store or composable logic, or i18n keys. Add new keys only for new UI text, such as "Collapse sidebar", in every locale.
- Don't rename CSS classes that views or tests rely on. Restyle them in place.
- Don't add a UI framework (Vuetify, PrimeVue, Tailwind, etc.) unless the user asks.
- Don't use the array index as a `v-for` key in new nav or layout code. Key on the route path.
- Don't redesign everything at once and test at the end. Get the shell working first, then the global patterns, then each view.
