<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-controls">
          <label class="budget-label" for="budget-range">
            {{ t('restocking.budget') }}: <strong>{{ formatCurrency(budget, currentCurrency) }}</strong>
          </label>
          <input
            id="budget-range"
            class="budget-range"
            type="range"
            min="0"
            :max="maxBudget"
            step="500"
            v-model.number="budget"
          />
          <input
            class="budget-number"
            type="number"
            min="0"
            :max="maxBudget"
            step="500"
            :value="budget"
            @input="onNumberInput"
            :aria-label="t('restocking.budget')"
          />
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value">{{ formatCurrency(selectedTotal, currentCurrency) }}</div>
        </div>
        <div :class="['stat-card', remaining < 0 ? 'danger' : 'warning']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(remaining, currentCurrency) }}</div>
        </div>
      </div>

      <div v-if="orderResult" class="alert alert-success banner">
        <span>
          {{ t('restocking.orderPlaced', {
            number: orderResult.order_number,
            date: formatDate(orderResult.expected_delivery)
          }) }}
        </span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="orderError" class="alert alert-error">{{ orderError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
          <button class="btn btn-primary" :disabled="!canSubmit" @click="placeOrder">
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="fetchError" class="error">{{ fetchError }}</div>
        <div v-else-if="items.length === 0" class="empty-state">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container" :class="{ refreshing: refreshing }">
          <table>
            <thead>
              <tr>
                <th class="col-check">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    @change="toggleAll($event.target.checked)"
                    aria-label="Select all"
                  />
                </th>
                <th>{{ t('restocking.item') }}</th>
                <th>{{ t('restocking.trend') }}</th>
                <th class="num">{{ t('restocking.currentDemand') }}</th>
                <th class="num">{{ t('restocking.forecastedDemand') }}</th>
                <th class="num">{{ t('restocking.quantity') }}</th>
                <th class="num">{{ t('restocking.unitCost') }}</th>
                <th class="num">{{ t('restocking.lineTotal') }}</th>
                <th class="num">{{ t('restocking.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku">
                <td class="col-check">
                  <input type="checkbox" v-model="selection[item.sku]" />
                </td>
                <td>
                  <strong>{{ translateProductName(item.name) }}</strong>
                  <div class="sku">{{ item.sku }}</div>
                </td>
                <td>
                  <span :class="['badge', trendClass(item.trend)]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.current_demand }}</td>
                <td class="num">{{ item.forecasted_demand }}</td>
                <td class="num">{{ item.quantity }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td class="num"><strong>{{ formatCurrency(item.line_total, currentCurrency) }}</strong></td>
                <td class="num">{{ t('restocking.leadTimeDays', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const STEP = 500
const DEBOUNCE_MS = 250
const roundUp = (n) => Math.ceil(n / STEP) * STEP

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const fetchError = ref(null)
    const refreshing = ref(false)
    const budget = ref(0)
    const maxBudget = ref(0)
    const items = ref([])
    const selection = ref({}) // sku -> boolean
    const submitting = ref(false)
    const orderResult = ref(null)
    const orderError = ref(null)

    let timer = null
    let requestId = 0 // guards against out-of-order responses

    const fetchRecommendations = async () => {
      const myRequest = ++requestId
      refreshing.value = true
      try {
        const data = await api.getRestockRecommendations(budget.value)
        if (myRequest !== requestId) return // a newer request superseded this one
        items.value = data.items
        // Tick everything whenever a new list arrives
        selection.value = Object.fromEntries(data.items.map(i => [i.sku, true]))
        fetchError.value = null
        return data
      } catch (err) {
        if (myRequest === requestId) {
          fetchError.value = err.response?.data?.detail || err.message
        }
      } finally {
        if (myRequest === requestId) refreshing.value = false
      }
    }

    const init = async () => {
      try {
        // Budget 0 is only used to learn the useful maximum
        const first = await api.getRestockRecommendations(0)
        maxBudget.value = roundUp(first.max_useful_budget)
        budget.value = Math.round(maxBudget.value / 2 / STEP) * STEP
        await fetchRecommendations()
      } catch (err) {
        error.value = err.response?.data?.detail || err.message
      } finally {
        loading.value = false
      }
    }

    // Debounced refetch on budget change (ignored until init has set the max)
    watch(budget, () => {
      if (loading.value) return
      orderResult.value = null
      clearTimeout(timer)
      timer = setTimeout(fetchRecommendations, DEBOUNCE_MS)
    })

    const onNumberInput = (e) => {
      const v = Number(e.target.value)
      const clamped = Math.min(Math.max(Number.isFinite(v) ? v : 0, 0), maxBudget.value)
      budget.value = clamped
      e.target.value = clamped // reflect clamping in the field even if budget didn't change
    }

    const selectedItems = computed(() => items.value.filter(i => selection.value[i.sku]))
    const selectedTotal = computed(() => selectedItems.value.reduce((s, i) => s + i.line_total, 0))
    const remaining = computed(() => budget.value - selectedTotal.value)
    const allSelected = computed(() => items.value.length > 0 && selectedItems.value.length === items.value.length)
    const canSubmit = computed(() => selectedItems.value.length > 0 && !submitting.value && !refreshing.value)

    const toggleAll = (checked) => {
      selection.value = Object.fromEntries(items.value.map(i => [i.sku, checked]))
    }

    const trendClass = (trend) => ({ increasing: 'success', stable: 'info', decreasing: 'warning' }[trend] || 'info')

    const formatDate = (dateString) => {
      const d = new Date(dateString)
      if (isNaN(d.getTime())) return ''
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return d.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const placeOrder = async () => {
      submitting.value = true
      orderError.value = null
      orderResult.value = null
      try {
        orderResult.value = await api.submitRestockOrder({
          budget: budget.value,
          items: selectedItems.value.map(i => ({ sku: i.sku, quantity: i.quantity }))
        })
      } catch (err) {
        orderError.value = err.response?.data?.detail || t('restocking.orderFailed')
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)
    onUnmounted(() => clearTimeout(timer))

    return {
      t, currentCurrency, translateProductName, formatCurrency, formatCurrencyWithDecimals,
      loading, error, fetchError, refreshing, budget, maxBudget, items, selection,
      submitting, orderResult, orderError, selectedTotal, remaining, allSelected, canSubmit,
      onNumberInput, toggleAll, trendClass, formatDate, placeOrder
    }
  }
}
</script>

<style scoped>
/* Buttons, alerts, empty state and card-subtitle come from the global styles in App.vue. */

/* Budget card: label/readout on top, slider and number input on one row */
.budget-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3) var(--space-4);
}

.budget-label {
  grid-column: 1 / -1;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}

/* Clear value readout */
.budget-label strong {
  margin-left: var(--space-2);
  color: var(--text);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  font-variant-numeric: tabular-nums;
}

.budget-range {
  width: 100%;
  min-width: 0;
  accent-color: var(--accent);
  cursor: pointer;
}

.budget-range:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-full);
}

/* Matches the global input look: 36px, --radius-md, --border, focus ring */
.budget-number {
  width: 120px;
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text);
  font-family: inherit;
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
  text-align: right;
  transition: border-color var(--duration) var(--ease), box-shadow var(--duration) var(--ease);
}

.budget-number:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

@media (max-width: 479px) {
  .budget-controls {
    grid-template-columns: minmax(0, 1fr);
  }

  .budget-number {
    width: 100%;
  }
}

/* Numeric columns right-aligned */
.num {
  text-align: right;
}

.col-check {
  width: 40px;
}

.sku {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

/* Dim the table while a new recommendation list is loading */
.refreshing {
  opacity: 0.6;
  transition: opacity var(--duration) var(--ease);
}

/* Success banner: global .alert-success supplies colours; this lays out the link */
.banner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.banner-link {
  color: var(--success);
  font-weight: var(--weight-semibold);
  text-decoration: underline;
}
</style>
