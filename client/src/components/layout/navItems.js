// Single source of truth for navigation. Used by the sidebar (rendering) and
// the top bar (page title) so they cannot drift apart. Keep in sync with the router.
export const navGroups = [
  {
    key: 'main',
    label: null,
    items: [{ to: '/', labelKey: 'nav.overview', icon: 'home' }]
  },
  {
    key: 'operations',
    label: 'nav.groupOperations',
    items: [
      { to: '/inventory', labelKey: 'nav.inventory', icon: 'box' },
      { to: '/orders', labelKey: 'nav.orders', icon: 'clipboard' },
      { to: '/restocking', labelKey: 'nav.restocking', icon: 'truck' }
    ]
  },
  {
    key: 'analytics',
    label: 'nav.groupAnalytics',
    items: [
      { to: '/spending', labelKey: 'nav.finance', icon: 'wallet' },
      { to: '/demand', labelKey: 'nav.demandForecast', icon: 'trending-up' },
      { to: '/reports', labelKey: 'nav.reports', icon: 'file-text' }
    ]
  }
]

export const allNavItems = navGroups.flatMap(g => g.items)

// "/" matches exactly; every other path matches by prefix on a segment boundary
export const isNavActive = (to, path) =>
  to === '/' ? path === '/' : path === to || path.startsWith(to + '/')
