<template>
  <svg
    class="nav-icon"
    viewBox="0 0 24 24"
    width="20"
    height="20"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <!-- Each icon is a list of path strings; keyed on the path data itself -->
    <path v-for="d in paths" :key="d" :d="d" />
  </svg>
</template>

<script>
import { computed } from 'vue'

// Simple outline shapes on a 24x24 grid
const ICONS = {
  home: ['M3 11l9-8 9 8', 'M5 10v10h14V10', 'M10 20v-6h4v6'],
  box: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'],
  clipboard: ['M9 4h6a1 1 0 011 1v1H8V5a1 1 0 011-1z', 'M8 6H6a1 1 0 00-1 1v13a1 1 0 001 1h12a1 1 0 001-1V7a1 1 0 00-1-1h-2', 'M9 12h6', 'M9 16h4'],
  truck: ['M2 6h12v11H2z', 'M14 10h4l4 3v4h-8', 'M6 20a2 2 0 100-4 2 2 0 000 4z', 'M18 20a2 2 0 100-4 2 2 0 000 4z'],
  wallet: ['M3 7a2 2 0 012-2h13v4', 'M3 7v11a2 2 0 002 2h15a1 1 0 001-1V10a1 1 0 00-1-1H5a2 2 0 01-2-2z', 'M16 14.5h.01'],
  'trending-up': ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'],
  'file-text': ['M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z', 'M14 3v5h5', 'M9 13h6', 'M9 17h6'],
  'chevron-left': ['M15 6l-6 6 6 6'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16']
}

export default {
  name: 'NavIcon',
  props: {
    name: { type: String, required: true }
  },
  setup(props) {
    const paths = computed(() => ICONS[props.name] || [])
    return { paths }
  }
}
</script>

<style scoped>
.nav-icon {
  flex-shrink: 0;
}
</style>
