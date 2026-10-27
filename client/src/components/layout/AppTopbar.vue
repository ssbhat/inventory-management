<template>
  <header class="topbar">
    <button
      type="button"
      class="topbar-menu"
      :aria-label="t('nav.openMenu')"
      :title="t('nav.openMenu')"
      aria-controls="app-sidebar"
      @click="$emit('open-menu')"
    >
      <NavIcon name="menu" />
    </button>
    <h1 class="topbar-title">{{ pageTitle }}</h1>
    <div class="topbar-actions">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </header>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../../composables/useI18n'
import NavIcon from './NavIcon.vue'
import LanguageSwitcher from '../LanguageSwitcher.vue'
import ProfileMenu from '../ProfileMenu.vue'
import { allNavItems, isNavActive } from './navItems'

export default {
  name: 'AppTopbar',
  components: { NavIcon, LanguageSwitcher, ProfileMenu },
  emits: ['open-menu', 'show-profile-details', 'show-tasks'],
  setup() {
    const route = useRoute()
    const { t } = useI18n()

    // Title comes from the same nav list as the sidebar; empty for unknown routes
    const pageTitle = computed(() => {
      const item = allNavItems.find(i => isNavActive(i.to, route.path))
      return item ? t(item.labelKey) : ''
    })

    return { t, pageTitle }
  }
}
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.topbar-menu {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.topbar-menu:hover {
  background: var(--surface-hover);
}

.topbar-menu:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

@media (max-width: 767px) {
  .topbar {
    padding: 0 var(--space-4);
    gap: var(--space-3);
  }

  .topbar-menu {
    display: inline-flex;
  }
}
</style>
