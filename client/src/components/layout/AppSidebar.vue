<template>
  <aside
    class="sidebar"
    :class="{ collapsed, 'mobile-open': mobileOpen }"
    id="app-sidebar"
  >
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true"></div>
      <div class="brand-text">
        <div class="brand-name">{{ t('nav.companyName') }}</div>
        <div class="brand-subtitle">{{ t('nav.subtitle') }}</div>
      </div>
    </div>

    <nav aria-label="Main" class="sidebar-nav">
      <div v-for="group in navGroups" :key="group.key" class="nav-group">
        <div v-if="group.label" class="nav-group-label">{{ t(group.label) }}</div>
        <!-- Both rendered; CSS swaps label for a thin divider in icons-only mode (not in the drawer) -->
        <div v-if="group.label" class="nav-group-divider" aria-hidden="true"></div>
        <router-link
          v-for="item in group.items"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
          :aria-current="isActive(item.to) ? 'page' : undefined"
          :aria-label="collapsed ? t(item.labelKey) : undefined"
          @mouseenter="showTip($event, t(item.labelKey))"
          @mouseleave="hideTip"
          @focus="showTip($event, t(item.labelKey))"
          @blur="hideTip"
        >
          <NavIcon :name="item.icon" />
          <span class="nav-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </div>
    </nav>

    <button
      type="button"
      class="sidebar-collapse"
      :aria-expanded="!collapsed"
      aria-controls="app-sidebar"
      :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
      @mouseenter="showTip($event, collapseText)"
      @mouseleave="hideTip"
      @focus="showTip($event, collapseText)"
      @blur="hideTip"
      @click="$emit('toggle-collapse')"
    >
      <NavIcon name="chevron-left" class="collapse-icon" />
      <span class="nav-label">{{ collapseText }}</span>
    </button>
  </aside>
  <!-- Single shared tooltip, position: fixed so the scrolling sidebar cannot clip it -->
  <div
    v-if="tip.visible"
    class="sidebar-tooltip"
    role="presentation"
    :style="{ top: tip.top + 'px', left: tip.left + 'px' }"
  >{{ tip.text }}</div>
  <div v-if="mobileOpen" class="sidebar-backdrop" @click="$emit('close-mobile')"></div>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../../composables/useI18n'
import NavIcon from './NavIcon.vue'
import { navGroups, isNavActive } from './navItems'

export default {
  name: 'AppSidebar',
  components: { NavIcon },
  props: {
    collapsed: { type: Boolean, default: false },
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['toggle-collapse', 'close-mobile'],
  setup(props) {
    const route = useRoute()
    const { t } = useI18n()
    const isActive = (to) => isNavActive(to, route.path)
    const collapseText = computed(() => props.collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar'))

    // Tooltip for icons-only mode. Placed from the hovered element's rect.
    const tip = ref({ visible: false, text: '', top: 0, left: 0 })
    const showTip = (event, text) => {
      // Only in icons-only desktop mode; the mobile drawer shows full labels
      if (!props.collapsed || window.innerWidth < 768) return
      const rect = event.currentTarget.getBoundingClientRect()
      tip.value = { visible: true, text, top: rect.top + rect.height / 2, left: rect.right }
    }
    const hideTip = () => { tip.value.visible = false }
    // Expanding/collapsing moves the items, so drop any stale tooltip
    watch(() => props.collapsed, hideTip)

    return { t, navGroups, isActive, collapseText, tip, showTip, hideTip }
  }
}
</script>

<style scoped>
/* Widths/labels animate over --duration; --duration is 0ms under prefers-reduced-motion */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 var(--space-2);
  margin-bottom: var(--space-6);
  overflow: hidden;
  transition: padding var(--duration) var(--ease);
}

.brand-mark {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--accent);
}

.brand-text {
  min-width: 0;
  margin-left: var(--space-3);
  white-space: nowrap;
  overflow: hidden;
  transition: opacity var(--duration) var(--ease), margin var(--duration) var(--ease);
}

.brand-name {
  color: var(--sidebar-active-text);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  color: var(--sidebar-text-muted);
  font-size: var(--text-xs);
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-group-label {
  padding: 0 var(--space-3);
  margin-bottom: var(--space-1);
  color: var(--sidebar-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.nav-group-divider {
  display: none;
  height: 1px;
  margin: 0 var(--space-2) var(--space-1);
  background: var(--sidebar-hover);
}

.nav-item,
.sidebar-collapse {
  display: flex;
  align-items: center;
  height: 40px;
  min-width: 40px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--sidebar-text);
  text-decoration: none;
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease),
    padding var(--duration) var(--ease);
}

.nav-label {
  margin-left: var(--space-3);
  overflow: hidden;
  white-space: nowrap;
  transition: opacity var(--duration) var(--ease), margin var(--duration) var(--ease);
}

.nav-item:hover,
.sidebar-collapse:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-active-text);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-active-text);
  box-shadow: inset 3px 0 0 var(--accent);
}

.nav-item:focus-visible,
.sidebar-collapse:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.nav-item.active:focus-visible {
  box-shadow: inset 3px 0 0 var(--accent), var(--focus-ring);
}

.sidebar-collapse {
  margin-top: var(--space-4);
  width: 100%;
}

.collapse-icon {
  transition: transform var(--duration) var(--ease);
}

/* Icons-only: label collapses to zero width and fades; icon is centered by padding
   ((sidebar inner width - icon width) / 2) so it does not jump during the animation */
.sidebar.collapsed .nav-item,
.sidebar.collapsed .sidebar-collapse {
  padding: 0 calc((var(--sidebar-width-collapsed) - 2 * var(--space-3) - 20px) / 2);
}

.sidebar.collapsed .nav-label,
.sidebar.collapsed .brand-text {
  opacity: 0;
  width: 0;
  margin-left: 0;
}

.sidebar.collapsed .sidebar-brand {
  padding: 0 calc((var(--sidebar-width-collapsed) - 2 * var(--space-3) - 28px) / 2);
}

.sidebar.collapsed .nav-group-label {
  display: none;
}

.sidebar.collapsed .nav-group-divider {
  display: block;
}

.sidebar.collapsed .collapse-icon {
  transform: rotate(180deg);
}

.sidebar-tooltip {
  position: fixed;
  z-index: 100;
  transform: translateY(-50%);
  margin-left: var(--space-2);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  background: var(--sidebar-bg);
  color: var(--sidebar-active-text);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  box-shadow: var(--shadow-md);
  pointer-events: none;
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 50;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
    box-shadow: var(--shadow-lg);
  }

  /* The drawer always shows full labels, whatever the desktop collapsed state */
  .sidebar.collapsed .nav-label,
  .sidebar.collapsed .brand-text {
    opacity: 1;
    width: auto;
    margin-left: var(--space-3);
  }

  .sidebar.collapsed .nav-item {
    padding: 0 var(--space-3);
  }

  .sidebar.collapsed .nav-group-label {
    display: block;
  }

  .sidebar.collapsed .nav-group-divider {
    display: none;
  }

  .sidebar.collapsed .sidebar-brand {
    padding: 0 var(--space-2);
  }

  .sidebar-collapse {
    display: none;
  }

  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgba(15, 23, 42, 0.4);
  }
}

/* The backdrop only exists for the drawer */
@media (min-width: 768px) {
  .sidebar-backdrop {
    display: none;
  }
}
</style>
