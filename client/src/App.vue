<template>
  <div class="app-shell" :class="{ 'is-collapsed': collapsed }">
    <AppSidebar
      :collapsed="collapsed"
      :mobile-open="mobileOpen"
      @toggle-collapse="toggleCollapse"
      @close-mobile="mobileOpen = false"
    />
    <div class="app-main">
      <AppTopbar
        @open-menu="mobileOpen = true"
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
      <FilterBar />
      <main class="app-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppTopbar from './components/layout/AppTopbar.vue'

// Wide screens (>= 1280px) default to a full sidebar; 768-1279px defaults to icons-only.
// The user's manual choice is remembered separately for each range.
const WIDE_QUERY = '(min-width: 1280px)'
const STORAGE_KEYS = { wide: 'sidebar-collapsed-wide', narrow: 'sidebar-collapsed-narrow' }

const readSaved = (range) => {
  try {
    const v = localStorage.getItem(STORAGE_KEYS[range])
    return v === null ? null : v === 'true'
  } catch (e) {
    return null
  }
}

const writeSaved = (range, value) => {
  try {
    localStorage.setItem(STORAGE_KEYS[range], String(value))
  } catch (e) {
    // Storage unavailable (private mode etc.): preference just isn't remembered
  }
}

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    AppSidebar,
    AppTopbar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const route = useRoute()

    // Sidebar state. 'range' is which breakpoint range the viewport is in.
    const wideQuery = window.matchMedia(WIDE_QUERY)
    const range = ref(wideQuery.matches ? 'wide' : 'narrow')
    // Saved choice for the current range if any, otherwise the range default
    const resolveCollapsed = (r) => {
      const saved = readSaved(r)
      return saved !== null ? saved : r === 'narrow'
    }
    const collapsed = ref(resolveCollapsed(range.value))
    const mobileOpen = ref(false)

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
      writeSaved(range.value, collapsed.value)
    }

    // Crossing 1280px live: switch range and apply that range's preference or default
    const onRangeChange = (e) => {
      range.value = e.matches ? 'wide' : 'narrow'
      collapsed.value = resolveCollapsed(range.value)
    }

    // Close the mobile drawer on navigation
    watch(() => route.path, () => { mobileOpen.value = false })

    const onKeydown = (e) => {
      if (e.key === 'Escape' && mobileOpen.value) mobileOpen.value = false
    }

    onMounted(() => {
      wideQuery.addEventListener('change', onRangeChange)
      document.addEventListener('keydown', onKeydown)
    })
    onUnmounted(() => {
      wideQuery.removeEventListener('change', onRangeChange)
      document.removeEventListener('keydown', onKeydown)
    })
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      collapsed,
      mobileOpen,
      toggleCollapse,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  line-height: 1.5;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- App shell ---------- */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--bg);
  transition: grid-template-columns var(--duration) var(--ease);
}

.app-shell.is-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

/* min-width: 0 stops wide tables from stretching the grid column */
.app-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}

@media (max-width: 767px) {
  .app-shell,
  .app-shell.is-collapsed {
    grid-template-columns: minmax(0, 1fr);
  }

  .app-content {
    padding: var(--space-4);
  }
}

/* ---------- Page header ---------- */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--weight-semibold);
  color: var(--text);
  line-height: 1.3;
  margin-bottom: var(--space-1);
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

/* ---------- KPI / stat cards ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5) var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--duration) var(--ease), box-shadow var(--duration) var(--ease);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: var(--weight-semibold);
  color: var(--text);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value { color: var(--warning); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

/* ---------- Cards ---------- */
.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--text);
}

.card-subtitle {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

/* ---------- Tables ---------- */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

/* Sticky header sticks to the top of .table-container's scroll area (or the page) */
thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--surface-sunken);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: var(--weight-semibold);
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border);
  color: var(--text);
  font-size: var(--text-sm);
}

tbody tr:first-child td {
  border-top: none;
}

tbody tr {
  transition: background-color var(--duration) var(--ease);
}

tbody tr:hover {
  background: var(--surface-hover);
}

/* ---------- Badges ---------- */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  line-height: 1.4;
  white-space: nowrap;
  background: var(--surface-sunken);
  color: var(--text-muted);
}

.badge.success,
.badge.increasing {
  background: var(--success-soft);
  color: var(--success);
}

.badge.info,
.badge.low {
  background: var(--info-soft);
  color: var(--info);
}

.badge.warning,
.badge.medium {
  background: var(--warning-soft);
  color: var(--warning);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--danger-soft);
  color: var(--danger);
}

.badge.stable {
  background: var(--surface-sunken);
  color: var(--text-muted);
}

/* ---------- Buttons ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  line-height: 1;
  white-space: nowrap;
  text-decoration: none;
  cursor: pointer;
  transition: background var(--duration) var(--ease), border-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  color: var(--accent-text);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border-color: var(--border-strong);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--surface-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text-muted);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--text);
}

/* ---------- States ---------- */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.empty-state {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.error {
  background: var(--danger-soft);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}

.alert {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-4);
}

.alert-success {
  background: var(--success-soft);
  border-color: var(--success);
  color: var(--success);
}

.alert-error {
  background: var(--danger-soft);
  border-color: var(--danger);
  color: var(--danger);
}
</style>
