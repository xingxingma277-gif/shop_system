<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
        <b>库存台账</b>
        <el-button v-if="showDashboardBack" link type="primary" @click="backToDashboard">返回看板</el-button>
      </div>
    </template>

    <el-alert
      v-if="contextMessage"
      :title="contextMessage"
      type="warning"
      :closable="false"
      style="margin-bottom:12px;"
    />

    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <el-select v-model="filters.warehouse_id" clearable placeholder="仓库" style="width:180px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select>
      <el-select v-model="filters.biz_type" clearable placeholder="业务类型" style="width:180px"><el-option label="销售出库" value="sale" /><el-option label="采购入库" value="purchase_receive" /><el-option label="采购退货" value="purchase_return" /><el-option label="库存调整" value="inventory_adjustment" /><el-option label="库存盘点" value="inventory_check" /><el-option label="调拨调出" value="inventory_transfer_out" /><el-option label="调拨调入" value="inventory_transfer_in" /></el-select>
      <el-input v-model="productName" placeholder="商品" style="width:200px" clearable :disabled="Boolean(routeProductId)" />
      <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" />
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column prop="warehouse_name" label="仓库" width="120" />
      <el-table-column prop="product_name" label="商品" min-width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="goProduct(row)">{{ row.product_name }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="change_qty" label="变动" width="100" />
      <el-table-column prop="after_qty" label="结存" width="100" />
      <el-table-column prop="biz_type" label="业务类型" width="140" />
      <el-table-column prop="note" label="备注" min-width="200" />
    </el-table>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listWarehouses } from '../api/warehouses'
import { listInventoryLedger } from '../api/inventory'

const route = useRoute()
const router = useRouter()
const rows = ref([])
const warehouses = ref([])
const productName = ref('')
const filters = reactive({ warehouse_id: null, biz_type: '', dateRange: [] })

const routeProductId = computed(() => {
  const raw = route.query.product_id
  if (raw == null || raw === '') return null
  const num = Number(raw)
  return Number.isFinite(num) ? num : null
})
const showDashboardBack = computed(() => route.query.source === 'dashboard')
const contextMessage = computed(() => {
  if (route.query.source !== 'dashboard') return ''
  if (route.query.context === 'low_stock' && productName.value) {
    return `当前来自看板低库存预警，已自动筛选商品“${productName.value}”的库存流水。`
  }
  if (route.query.context === 'low_stock') {
    return '当前来自看板低库存预警。'
  }
  return '当前来自看板经营上下文。'
})

function applyRouteQuery() {
  filters.warehouse_id = route.query.warehouse_id ? Number(route.query.warehouse_id) : null
  filters.biz_type = typeof route.query.biz_type === 'string' ? route.query.biz_type : ''
  productName.value = typeof route.query.product_name === 'string' ? route.query.product_name : ''
  if (typeof route.query.start_date === 'string' && typeof route.query.end_date === 'string') {
    filters.dateRange = [dayjs(route.query.start_date).toDate(), dayjs(route.query.end_date).toDate()]
  }
}

function backToDashboard() {
  const query = {}
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  router.push({ path: '/dashboard', query })
}

function goProduct(row) {
  if (!row?.product_name) return
  const query = { q: row.product_name, return_to: 'inventory-ledger' }
  if (typeof route.query.product_id === 'string') query.product_id = route.query.product_id
  if (typeof route.query.product_name === 'string') query.product_name = route.query.product_name
  if (typeof route.query.warehouse_id === 'string') query.warehouse_id = route.query.warehouse_id
  if (typeof route.query.biz_type === 'string') query.biz_type = route.query.biz_type
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  if (typeof route.query.start_date === 'string') query.start_date = route.query.start_date
  if (typeof route.query.end_date === 'string') query.end_date = route.query.end_date
  if (typeof route.query.source === 'string') query.source = route.query.source
  if (typeof route.query.context === 'string') query.context = route.query.context
  router.push({ path: '/products', query })
}

async function load() {
  const data = await listInventoryLedger({
    warehouse_id: filters.warehouse_id || undefined,
    product_id: routeProductId.value || undefined,
    biz_type: filters.biz_type || undefined,
    start_date: filters.dateRange?.[0] ? dayjs(filters.dateRange[0]).toISOString() : undefined,
    end_date: filters.dateRange?.[1] ? dayjs(filters.dateRange[1]).toISOString() : undefined,
  })
  let items = data.items || []
  if (!routeProductId.value && productName.value) {
    items = items.filter((item) => item.product_name === productName.value)
  }
  rows.value = items
}

watch(() => route.query, async () => {
  applyRouteQuery()
  await load()
})

onMounted(async () => {
  applyRouteQuery()
  warehouses.value = await listWarehouses({})
  await load()
})
</script>
