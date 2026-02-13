<template>
  <el-card>
    <template #header>
      <div style="font-weight:700">交易记录</div>
    </template>

    <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
      <el-date-picker v-model="dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
      <el-select v-model="filters.type" clearable placeholder="类型" style="width:120px">
        <el-option label="开单" value="sale" />
        <el-option label="收款" value="payment" />
      </el-select>
      <el-input v-model="filters.q" placeholder="客户名/单号/备注" style="width:220px" clearable />
      <el-button @click="quickDays(7)">近7天</el-button>
      <el-button @click="quickDays(30)">近30天</el-button>
      <el-button @click="thisMonth">本月</el-button>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="occurred_at" label="时间" min-width="160"><template #default="{row}">{{ fmt(row.occurred_at) }}</template></el-table-column>
      <el-table-column prop="type" label="类型" width="90"><template #default="{row}">{{ row.type === 'sale' ? '开单' : '收款' }}</template></el-table-column>
      <el-table-column prop="customer_name" label="客户" min-width="160"><template #default="{row}"><router-link :to="`/customers/${row.customer_id}`">{{ row.customer_name }}</router-link></template></el-table-column>
      <el-table-column prop="sale_no" label="关联单号" min-width="160" />
      <el-table-column prop="amount" label="金额" width="110" />
      <el-table-column label="状态" width="120">
        <template #default="{row}">
          <span v-if="row.type==='sale'">{{ statusText(row.status) }}</span>
          <span v-else>已入账</span>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
    </el-table>

    <div style="display:flex; justify-content:flex-end; margin-top:12px;">
      <el-pagination background layout="total, prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="onPage" />
    </div>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, ref, reactive } from 'vue'
import { listTransactions } from '../api/transactions'

const dateRange = ref([dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()])
const filters = reactive({ q: '', type: '' })
const rows = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fmt = (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清' }[v] || '-')

function quickDays(days) {
  dateRange.value = [dayjs().subtract(days, 'day').toDate(), dayjs().endOf('day').toDate()]
}
function thisMonth() {
  dateRange.value = [dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()]
}
function onPage(p) {
  page.value = p
  load()
}

async function load() {
  const data = await listTransactions({
    page: page.value,
    page_size: pageSize.value,
    start_date: dateRange.value?.[0] ? dayjs(dateRange.value[0]).format('YYYY-MM-DD') : undefined,
    end_date: dateRange.value?.[1] ? dayjs(dateRange.value[1]).format('YYYY-MM-DD') : undefined,
    q: filters.q || undefined,
    type: filters.type || undefined,
  })
  rows.value = data.items || []
  total.value = data.meta?.total || 0
}

onMounted(load)
</script>
