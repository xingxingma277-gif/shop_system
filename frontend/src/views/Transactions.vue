<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
        <div style="font-weight:700">交易记录</div>
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

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="销售记录" name="sales">
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
          <el-date-picker v-model="salesFilters.dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
          <el-input v-model="salesFilters.q" placeholder="单号/客户名/商品名" style="width:240px" clearable />
          <el-select v-model="salesFilters.status" clearable placeholder="收款状态" style="width:140px">
            <el-option label="未结清" value="unpaid" />
            <el-option label="部分结清" value="partial" />
            <el-option label="已结清" value="paid" />
          </el-select>
          <el-button type="primary" @click="loadSales">查询</el-button>
        </div>

        <el-table :data="salesRows" border>
          <el-table-column prop="occurred_at" label="时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.occurred_at) }}</template></el-table-column>
          <el-table-column prop="sale_no" label="单号" min-width="150">
            <template #default="{row}">
               <el-button link type="primary" @click="goSale(row.sale_id)">{{ row.sale_no }}</el-button>
               <el-tag v-if="row.order_stage === 'QUOTE'" type="info" size="small" style="margin-left:4px">报价单</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="customer_name" label="客户" min-width="160"><template #default="{row}"><el-button link type="primary" @click="goCustomer(row.customer_id)">{{ row.customer_name }}</el-button></template></el-table-column>
          <el-table-column prop="total_amount" label="应收" width="100" />
          <el-table-column prop="paid_amount" label="已收" width="100" />
          <el-table-column prop="balance" label="未收" width="100" />
          <el-table-column prop="status" label="收款状态" width="120">
            <template #default="{row}">
              <el-tag v-if="row.status==='paid'" type="success">已结清</el-tag>
              <el-tag v-else-if="row.status==='partial'" type="warning">部分结清</el-tag>
              <el-tag v-else type="danger">未结清</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100"><template #default="{row}"><el-button link @click="goSale(row.sale_id)">详情</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="后续还款记录" name="payments">
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
          <el-date-picker v-model="payFilters.dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
          <el-input v-model="payFilters.q" placeholder="客户名/订单号" style="width:220px" clearable />
          <el-select v-model="payFilters.method" clearable placeholder="收款方式" style="width:140px">
            <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
          <el-button type="primary" @click="loadPayments">查询</el-button>
        </div>

        <el-table :data="payRows" border>
          <el-table-column prop="occurred_at" label="还款时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.occurred_at) }}</template></el-table-column>
          <el-table-column prop="customer_name" label="客户" min-width="160"><template #default="{row}"><el-button link type="primary" @click="goCustomer(row.customer_id)">{{ row.customer_name }}</el-button></template></el-table-column>
          <el-table-column prop="method" label="方式" width="110"><template #default="{row}">{{ paymentMethodText(row.method) }}</template></el-table-column>
          <el-table-column prop="amount" label="金额" width="100" />
          <el-table-column label="关联订单" min-width="220">
            <template #default="{row}">{{ foldSaleNos(row.sale_nos) }}</template>
          </el-table-column>
          <el-table-column prop="note" label="备注" min-width="160" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <div style="display:flex; justify-content:flex-end; margin-top:12px;">
      <el-pagination background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
    </div>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listTransactionPayments, listTransactionSales } from '../api/transactions'
import { formatDateTime } from '../utils/format'
import { useDictsStore } from '../stores/dicts'

const router = useRouter()
const route = useRoute()
const dicts = useDictsStore()
const paymentMethods = computed(() => dicts.paymentMethods)

const tab = ref('sales')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const salesRows = ref([])
const payRows = ref([])

const salesFilters = reactive({
  dateRange: [dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()],
  q: '',
  status: '',
})

const payFilters = reactive({
  dateRange: [dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()],
  q: '',
  method: '',
})

const statusTextMap = {
  unpaid: '未结清',
  partial: '部分结清',
  paid: '已结清',
}

const showDashboardBack = computed(() => route.query.source === 'dashboard')
const contextMessage = computed(() => {
  if (route.query.source !== 'dashboard') return ''
  if (route.query.context === 'ar_aging' || route.query.status === 'unpaid') {
    return `当前来自看板预警，已自动切换到销售记录，并按“${statusTextMap[salesFilters.status] || '未结清'}”筛选。`
  }
  if (tab.value === 'payments') {
    return '当前来自看板经营上下文，已自动切换到后续还款记录。'
  }
  return '当前来自看板经营上下文。'
})

function paymentMethodText(v) {
  const f = dicts.paymentMethods.find(m => m.value === v)
  return f ? f.label : (v || '-')
}

function applyRouteQuery() {
  const nextTab = typeof route.query.tab === 'string' && ['sales', 'payments'].includes(route.query.tab)
    ? route.query.tab
    : 'sales'
  tab.value = nextTab
  salesFilters.status = typeof route.query.status === 'string' ? route.query.status : ''
  if (typeof route.query.start_date === 'string' && typeof route.query.end_date === 'string') {
    salesFilters.dateRange = [dayjs(route.query.start_date).toDate(), dayjs(route.query.end_date).toDate()]
    payFilters.dateRange = [dayjs(route.query.start_date).toDate(), dayjs(route.query.end_date).toDate()]
  }
}

function refreshByTab() {
  page.value = 1
  return tab.value === 'sales' ? loadSales() : loadPayments()
}

function onPage(p) {
  page.value = p
  tab.value === 'sales' ? loadSales() : loadPayments()
}

function onTabChange() {
  refreshByTab()
}

function backToDashboard() {
  const query = {}
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  router.push({ path: '/dashboard', query })
}

async function loadSales() {
  const data = await listTransactionSales({
    page: page.value,
    page_size: pageSize.value,
    start_date: salesFilters.dateRange?.[0] ? dayjs(salesFilters.dateRange[0]).format('YYYY-MM-DD') : undefined,
    end_date: salesFilters.dateRange?.[1] ? dayjs(salesFilters.dateRange[1]).format('YYYY-MM-DD') : undefined,
    q: salesFilters.q || undefined,
    status: salesFilters.status || undefined,
    sort_by: 'date_desc',
  })
  salesRows.value = data.items || []
  total.value = data.meta?.total || 0
}

async function loadPayments() {
  const data = await listTransactionPayments({
    page: page.value,
    page_size: pageSize.value,
    start_date: payFilters.dateRange?.[0] ? dayjs(payFilters.dateRange[0]).format('YYYY-MM-DD') : undefined,
    end_date: payFilters.dateRange?.[1] ? dayjs(payFilters.dateRange[1]).format('YYYY-MM-DD') : undefined,
    q: payFilters.q || undefined,
    method: payFilters.method || undefined,
  })
  payRows.value = data.items || []
  total.value = data.meta?.total || 0
}

const foldSaleNos = (list) => !list?.length ? '-' : (list.length <= 2 ? list.join('、') : `${list.slice(0, 2).join('、')} +${list.length - 2}`)
const goSale = (id) => {
  const query = { return_to: 'transactions' }
  if (typeof route.query.tab === 'string') query.tab = route.query.tab
  if (typeof route.query.status === 'string') query.status = route.query.status
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  if (typeof route.query.start_date === 'string') query.start_date = route.query.start_date
  if (typeof route.query.end_date === 'string') query.end_date = route.query.end_date
  if (typeof route.query.source === 'string') query.source = route.query.source
  if (typeof route.query.context === 'string') query.context = route.query.context
  router.push({ path: `/sales/${id}`, query })
}
const goCustomer = (id) => router.push(`/customers/${id}`)

watch(() => route.query, async () => {
  applyRouteQuery()
  await refreshByTab()
})

onMounted(async () => {
  applyRouteQuery()
  await refreshByTab()
})
</script>
