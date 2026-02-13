<template>
  <el-card>
    <template #header><div style="font-weight:700">交易记录</div></template>

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="销售记录" name="sales">
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
          <el-date-picker v-model="salesFilters.dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
          <el-input v-model="salesFilters.q" placeholder="单号/客户名/商品名" style="width:240px" clearable />
          <el-select v-model="salesFilters.status" clearable placeholder="状态" style="width:140px">
            <el-option label="未结清" value="unpaid" />
            <el-option label="部分结清" value="partial" />
            <el-option label="已结清" value="paid" />
          </el-select>
          <el-button type="primary" @click="loadSales">查询</el-button>
        </div>

        <el-table :data="salesRows" border>
          <el-table-column prop="occurred_at" label="时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.occurred_at) }}</template></el-table-column>
          <el-table-column prop="sale_no" label="单号" min-width="150"><template #default="{row}"><el-button link type="primary" @click="goSale(row.sale_id)">{{ row.sale_no }}</el-button></template></el-table-column>
          <el-table-column prop="customer_name" label="客户" min-width="160"><template #default="{row}"><el-button link type="primary" @click="goCustomer(row.customer_id)">{{ row.customer_name }}</el-button></template></el-table-column>
          <el-table-column prop="total_amount" label="应收" width="100" />
          <el-table-column prop="paid_amount" label="已收" width="100" />
          <el-table-column prop="balance" label="未收" width="100" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{row}">
              <el-tag v-if="row.status==='paid'" type="success">已结清</el-tag>
              <el-tag v-else-if="row.status==='partial'" type="warning">部分结清</el-tag>
              <el-tag v-else type="danger">未结清</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100"><template #default="{row}"><el-button link @click="goSale(row.sale_id)">详情</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="还款记录" name="payments">
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
          <el-date-picker v-model="payFilters.dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
          <el-input v-model="payFilters.q" placeholder="客户名/订单号" style="width:220px" clearable />
          <el-select v-model="payFilters.method" clearable placeholder="方式" style="width:140px">
            <el-option label="现金" value="cash" />
            <el-option label="微信" value="wechat" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="转账" value="transfer" />
          </el-select>
          <el-button type="primary" @click="loadPayments">查询</el-button>
        </div>

        <el-table :data="payRows" border>
          <el-table-column prop="occurred_at" label="时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.occurred_at) }}</template></el-table-column>
          <el-table-column prop="customer_name" label="客户" min-width="160"><template #default="{row}"><el-button link type="primary" @click="goCustomer(row.customer_id)">{{ row.customer_name }}</el-button></template></el-table-column>
          <el-table-column prop="method" label="方式" width="110" />
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
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listTransactionPayments, listTransactionSales } from '../api/transactions'
import { formatDateTime } from '../utils/format'

const router = useRouter()
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

function onPage(p) {
  page.value = p
  tab.value === 'sales' ? loadSales() : loadPayments()
}

function onTabChange() {
  page.value = 1
  tab.value === 'sales' ? loadSales() : loadPayments()
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
const goSale = (id) => router.push(`/sales/${id}`)
const goCustomer = (id) => router.push(`/customers/${id}`)

onMounted(loadSales)
</script>
