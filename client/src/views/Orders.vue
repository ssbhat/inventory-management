<template>
  <div class="orders">
    <div class="page-header">
      <h2>{{ t('orders.title') }}</h2>
      <p>{{ t('orders.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">{{ t('orders.submittedOrders') }} ({{ submittedOrders.length }})</h3>
            <p class="card-subtitle">{{ t('orders.submittedOrdersDescription') }}</p>
          </div>
        </div>
        <div v-if="submittedError" class="error">{{ submittedError }}</div>
        <div v-else-if="submittedOrders.length === 0" class="empty-state">{{ t('orders.noSubmittedOrders') }}</div>
        <div v-else class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-date">{{ t('orders.submittedDate') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-status col-num">{{ t('orders.leadTime') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <th class="col-value col-num">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-date">{{ formatDate(order.submitted_date) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="item in order.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatCurrency(item.unit_cost, currentCurrency) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status"><span class="badge info">{{ t('status.submitted') }}</span></td>
                <td class="col-status col-num">
                  <span class="badge info lead-time">{{ t('orders.leadTimeDays', { days: order.lead_time_days }) }}</span>
                </td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value col-num"><strong>{{ formatCurrency(order.total_value, currentCurrency) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.allOrders') }} ({{ orders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th class="col-customer">{{ t('orders.table.customer') }}</th>
                <th class="col-items">{{ t('orders.table.items') }}</th>
                <th class="col-status">{{ t('orders.table.status') }}</th>
                <th class="col-date">{{ t('orders.table.orderDate') }}</th>
                <th class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <th class="col-value col-num">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-dropdown">
                      <div v-for="(item, idx) in order.items" :key="idx" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ currencySymbol }}{{ item.unit_price }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date">{{ formatDate(order.order_date) }}</td>
                <td class="col-date">{{ formatDate(order.expected_delivery) }}</td>
                <td class="col-value col-num"><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

export default {
  name: 'Orders',
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })
    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])
    // Submitted restock orders: independent of global filters, loaded once
    const submittedOrders = ref([])
    const submittedError = ref(null)

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date)
          const dateB = new Date(b.order_date)
          return dateA - dateB
        })
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const d = new Date(dateString)
      if (isNaN(d.getTime())) return ''
      return d.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadSubmittedOrders = async () => {
      try {
        submittedOrders.value = await api.getSubmittedOrders()
      } catch (err) {
        submittedError.value = 'Failed to load submitted orders: ' + err.message
      }
    }

    onMounted(() => {
      loadOrders()
      loadSubmittedOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currencySymbol,
      currentCurrency,
      formatCurrency,
      submittedOrders,
      submittedError,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
/* Fixed table layout to prevent column shifting */
.orders-table {
  table-layout: fixed;
  width: 100%;
  min-width: 960px; /* keeps fixed columns readable; .table-container scrolls below this */
}

/* Column widths */
.col-order-number { width: 130px; }
.col-customer { width: 180px; }
.col-items { width: 200px; }
.col-status { width: 130px; }
.col-date { width: 140px; }
.col-value { width: 120px; }

/* Numeric columns (money, lead time) are right-aligned */
.col-num { text-align: right; }

/* Lead time badge: tabular numerals and a slightly larger size so it reads clearly */
.lead-time {
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-3);
  font-variant-numeric: tabular-nums;
}

/* Items details styling */
.items-details {
  position: relative;
}

.items-summary {
  cursor: pointer;
  color: var(--accent);
  font-weight: var(--weight-medium);
  list-style: none;
  user-select: none;
  display: inline-block;
  border-radius: var(--radius-sm);
}

.items-summary::-webkit-details-marker {
  display: none;
}

.items-summary::before {
  content: '\25B6';
  display: inline-block;
  margin-right: var(--space-2);
  font-size: var(--text-xs);
  transition: transform var(--duration) var(--ease);
}

.items-details[open] .items-summary::before {
  transform: rotate(90deg);
}

.items-summary:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}

.items-summary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* Dropdown container: popover, so it gets the large shadow */
.items-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--space-2);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-3);
  z-index: 10;
  min-width: 300px;
  max-width: 400px;
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-bottom: 1px solid var(--border);
}

.item-entry:last-child {
  border-bottom: none;
}

.item-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text);
}

.item-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
}
</style>
