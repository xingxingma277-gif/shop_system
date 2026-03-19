<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
        <b>经营报表</b>
        <el-button v-if="showDashboardBack" link type="primary" @click="backToDashboard">返回看板</el-button>
      </div>
    </template>

    <el-alert
      v-if="contextMessage"
      :title="contextMessage"
      type="info"
      :closable="false"
      style="margin-bottom:12px;"
    />

    <el-tabs v-model="tab">
      <el-tab-pane label="应付汇总" name="ap">
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
          <el-select v-model="apFilters.supplier_id" clearable filterable placeholder="供应商" style="width:240px"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select>
          <el-date-picker v-model="apFilters.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" />
          <el-button type="primary" @click="loadAp">查询</el-button>
        </div>
        <el-alert :title="`采购总额：${apSummary.total_purchase_amount || 0}，已付：${apSummary.total_paid_amount || 0}，应付：${apSummary.total_ap_amount || 0}`" type="info" :closable="false" style="margin-bottom:8px;" />
        <el-table :data="apRows" border>
          <el-table-column prop="purchase_no" label="采购单号" min-width="140" />
          <el-table-column prop="supplier_name" label="供应商" min-width="140" />
          <el-table-column prop="total_amount" label="采购总额" width="110" />
          <el-table-column prop="paid_amount" label="已付" width="100" />
          <el-table-column prop="ap_amount" label="应付" width="100" />
          <el-table-column prop="status" label="状态" width="130" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="AP Aging" name="aging">
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
          <el-select v-model="agingFilters.supplier_id" clearable filterable placeholder="供应商" style="width:240px"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select>
          <el-date-picker v-model="agingFilters.as_of" type="date" placeholder="账龄截止日" />
          <el-button type="primary" @click="loadAging">查询</el-button>
        </div>
        <el-alert :title="`0-30天：${agingSummary['0_30'] || 0}，31-60天：${agingSummary['31_60'] || 0}，61-90天：${agingSummary['61_90'] || 0}，90+天：${agingSummary['90_plus'] || 0}`" type="warning" :closable="false" style="margin-bottom:8px;" />
        <el-table :data="agingRows" border>
          <el-table-column prop="purchase_no" label="采购单号" min-width="140">
            <template #default="{ row }">
              <el-button link type="primary" @click="goPurchase(row.purchase_id)">{{ row.purchase_no }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="supplier_name" label="供应商" min-width="140" />
          <el-table-column prop="age_days" label="账龄(天)" width="100" />
          <el-table-column prop="bucket" label="账龄区间" width="120" />
          <el-table-column prop="ap_amount" label="应付金额" width="120" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="库存流水汇总" name="inventory">
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
          <el-select v-model="invFilters.warehouse_id" clearable placeholder="仓库" style="width:220px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select>
          <el-date-picker v-model="invFilters.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" />
          <el-button type="primary" @click="loadInventory">查询</el-button>
        </div>
        <el-alert :title="`入库总量：${invSummary.in_qty || 0}，出库总量：${invSummary.out_qty || 0}，流水数：${invSummary.count || 0}`" type="success" :closable="false" style="margin-bottom:8px;" />
        <el-table :data="invRows" border>
          <el-table-column prop="created_at" label="时间" min-width="170" />
          <el-table-column prop="warehouse_name" label="仓库" width="120" />
          <el-table-column prop="biz_type" label="业务类型" width="140" />
          <el-table-column prop="change_qty" label="变动量" width="100" />
          <el-table-column prop="after_qty" label="结存" width="100" />
          <el-table-column prop="note" label="备注" min-width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApAging, getApSummary, getInventorySummary } from '../api/reports'
import { listSuppliers } from '../api/suppliers'
import { listWarehouses } from '../api/warehouses'

const route = useRoute()
const router = useRouter()
const tab = ref('ap')

const suppliers = ref([])
const warehouses = ref([])

const apRows = ref([])
const apSummary = reactive({ total_purchase_amount: 0, total_paid_amount: 0, total_ap_amount: 0 })
const apFilters = reactive({ supplier_id: null, dateRange: [] })

const agingRows = ref([])
const agingSummary = reactive({ '0_30': 0, '31_60': 0, '61_90': 0, '90_plus': 0 })
const agingFilters = reactive({ supplier_id: null, as_of: null })

const invRows = ref([])
const invSummary = reactive({ in_qty: 0, out_qty: 0, count: 0 })
const invFilters = reactive({ warehouse_id: null, dateRange: [] })

const showDashboardBack = computed(() => route.query.source === 'dashboard')
const contextMessage = computed(() => {
  if (route.query.source !== 'dashboard') return ''
  if (route.query.context === 'ap_aging' || tab.value === 'aging') {
    return '当前来自看板预警，已自动切换到 AP Aging 视图。'
  }
  return '当前来自看板经营上下文。'
})

async function loadAp() {
  const data = await getApSummary({
    supplier_id: apFilters.supplier_id || undefined,
    start_date: apFilters.dateRange?.[0] ? dayjs(apFilters.dateRange[0]).toISOString() : undefined,
    end_date: apFilters.dateRange?.[1] ? dayjs(apFilters.dateRange[1]).toISOString() : undefined,
  })
  apRows.value = data.items || []
  Object.assign(apSummary, data.summary || {})
}

async function loadAging() {
  const data = await getApAging({
    supplier_id: agingFilters.supplier_id || undefined,
    as_of: agingFilters.as_of ? dayjs(agingFilters.as_of).toISOString() : undefined,
  })
  agingRows.value = data.items || []
  Object.assign(agingSummary, data.summary || {})
}

async function loadInventory() {
  const data = await getInventorySummary({
    warehouse_id: invFilters.warehouse_id || undefined,
    start_date: invFilters.dateRange?.[0] ? dayjs(invFilters.dateRange[0]).toISOString() : undefined,
    end_date: invFilters.dateRange?.[1] ? dayjs(invFilters.dateRange[1]).toISOString() : undefined,
  })
  invRows.value = data.items || []
  Object.assign(invSummary, data.summary || {})
}

function applyRouteQuery() {
  const nextTab = typeof route.query.tab === 'string' ? route.query.tab : 'ap'
  if (['ap', 'aging', 'inventory'].includes(nextTab)) tab.value = nextTab
  if (typeof route.query.start_date === 'string' && typeof route.query.end_date === 'string') {
    const dateRange = [dayjs(route.query.start_date).toDate(), dayjs(route.query.end_date).toDate()]
    apFilters.dateRange = dateRange
    invFilters.dateRange = dateRange
  }
}

function backToDashboard() {
  const query = {}
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  router.push({ path: '/dashboard', query })
}

function goPurchase(id) {
  if (!id) return
  router.push(`/purchases/${id}`)
}

watch(() => route.query, applyRouteQuery)

onMounted(async () => {
  applyRouteQuery()
  suppliers.value = await listSuppliers({})
  warehouses.value = await listWarehouses({})
  await loadAp()
  await loadAging()
  await loadInventory()
})
</script>
