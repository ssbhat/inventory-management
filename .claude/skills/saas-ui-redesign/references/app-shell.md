# App shell reference

These are starting points. Adapt them to the project's own component style. If the project uses `export default { setup() }` instead of `<script setup>`, match that. Keep the existing i18n (`t(...)`) and the existing header widgets.

## App.vue (shell)

```vue
<template>
  <div class="app-shell" :class="{ 'is-collapsed': collapsed }">
    <AppSidebar
      :collapsed="collapsed"
      :mobile-open="mobileOpen"
      @toggle-collapse="toggleCollapse"
      @close-mobile="mobileOpen = false"
    />
    <div class="app-main">
      <AppTopbar @open-menu="mobileOpen = true">
        <!-- Existing header widgets move here unchanged -->
      </AppTopbar>
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>
```

The shell needs this state:
- `collapsed` starts from `localStorage`, read inside a try/catch. If nothing is saved, default to `window.innerWidth < 1024`. Save it again whenever it changes, also inside a try/catch.
- `mobileOpen` is set back to false on every route change, using `watch(() => route.path, ...)`.

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  background: var(--bg);
  transition: grid-template-columns var(--duration) var(--ease);
}
.app-shell.is-collapsed { grid-template-columns: var(--sidebar-width-collapsed) 1fr; }
.app-main { min-width: 0; display: flex; flex-direction: column; }  /* min-width:0 stops tables from widening the grid */
.app-content {
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}
@media (max-width: 767px) {
  .app-shell, .app-shell.is-collapsed { grid-template-columns: 1fr; }
  .app-content { padding: var(--space-4); }
}
```

## AppSidebar.vue

Build every nav link from one array, so the sidebar and the top bar title can't drift apart:

```js
// Keep in sync with the router; key v-for on `to`, never the index.
const navGroups = [
  { label: null, items: [
    { to: '/', labelKey: 'nav.overview', icon: 'home' },
    { to: '/inventory', labelKey: 'nav.inventory', icon: 'box' },
  ]},
  { label: 'nav.groupOperations', items: [ /* ... */ ] },
]
```

Mark a link active when the route matches exactly for `/`, and by prefix for every other path:

```js
const isActive = (to) => to === '/' ? route.path === '/' : route.path.startsWith(to)
```

The markup structure:

```vue
<aside class="sidebar" :class="{ collapsed, 'mobile-open': mobileOpen }">
  <div class="sidebar-brand">…logo + name (name hidden when collapsed)…</div>
  <nav aria-label="Main" class="sidebar-nav">
    <div v-for="group in navGroups" :key="group.label || 'main'" class="nav-group">
      <div v-if="group.label && !collapsed" class="nav-group-label">{{ t(group.label) }}</div>
      <router-link
        v-for="item in group.items" :key="item.to" :to="item.to"
        class="nav-item" :class="{ active: isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
        :title="collapsed ? t(item.labelKey) : undefined"
      >
        <NavIcon :name="item.icon" />
        <span class="nav-label">{{ t(item.labelKey) }}</span>
      </router-link>
    </div>
  </nav>
  <button class="sidebar-collapse" :aria-expanded="!collapsed" @click="$emit('toggle-collapse')">…</button>
</aside>
<div v-if="mobileOpen" class="sidebar-backdrop" @click="$emit('close-mobile')" />
```

Key styles:

```css
.sidebar {
  position: sticky; top: 0; height: 100vh;
  display: flex; flex-direction: column;
  background: var(--sidebar-bg); color: var(--sidebar-text);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto; overflow-x: hidden;
}
.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  height: 40px; padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text); text-decoration: none;
  font-size: var(--text-sm); font-weight: var(--weight-medium);
  transition: background var(--duration) var(--ease);
}
.nav-item:hover { background: var(--sidebar-hover); }
.nav-item.active { background: var(--sidebar-active-bg); color: var(--sidebar-active-text); box-shadow: inset 3px 0 0 var(--accent); }
.nav-item:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.sidebar.collapsed .nav-label,
.sidebar.collapsed .nav-group-label { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; }

@media (max-width: 767px) {
  .sidebar {
    position: fixed; inset: 0 auto 0 0; z-index: 50;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease);
    box-shadow: var(--shadow-lg);
  }
  .sidebar.mobile-open { transform: translateX(0); }
  .sidebar.collapsed .nav-label { display: inline; }   /* the drawer always shows labels */
  .sidebar-backdrop { position: fixed; inset: 0; z-index: 40; background: rgba(15, 23, 42, 0.4); }
  .sidebar-collapse { display: none; }
}
```

Esc closes the drawer: add a `keydown` listener in `onMounted` and remove it in `onUnmounted`.

## Icons (no dependency)

Make one small `NavIcon.vue` that maps names to inline SVG paths. Use a 24×24 viewBox, `fill="none"`, `stroke="currentColor"`, `stroke-width="1.75"`, `stroke-linecap="round"`, `aria-hidden="true"`, and size it at 18–20px. Simple outline shapes work well: home, box, clipboard, wallet, trending-up, file-text, truck, chevron-left.

## AppTopbar.vue

```css
.topbar {
  position: sticky; top: 0; z-index: 30;
  height: var(--topbar-height);
  display: flex; align-items: center; gap: var(--space-4);
  padding: 0 var(--space-8);
  background: var(--surface); border-bottom: 1px solid var(--border);
}
.topbar-title { font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: var(--space-3); }
.topbar-menu { display: none; }          /* only shown on mobile */
@media (max-width: 767px) {
  .topbar { padding: 0 var(--space-4); }
  .topbar-menu { display: inline-flex; }
}
```

If the app has a global filter bar, choose one of these and keep its component and logic unchanged:
- put it in the top bar if it's compact, or
- put it as a sticky strip directly under the top bar if it has several selects.
