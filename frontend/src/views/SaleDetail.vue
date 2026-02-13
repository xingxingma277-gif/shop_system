<template>
  <el-card v-if="sale">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div style="font-weight:700">订单详情</div>
        <div style="display:flex;gap:8px;">
          <el-button @click="onPrint">打印</el-button>
          <el-button type="primary" plain @click="onContinue">继续开单</el-button>
          <el-button type="primary" @click="onProfile">查看客户档案</el-button>
        </div>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="单号">{{ sale.sale_no }}</el-descriptions-item>
      <el-descriptions-item label="日期时间">{{ fmt(sale.sale_date) }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ sale.customer_name }}</el-descriptions-item>
      <el-descriptions-item label="拿货人" v-if="sale.buyer_name">{{ sale.buyer_name }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ sale.note || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />
    <el-table :data="sale.items || []" border>
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="sku" label="SKU" min-width="120" />
      <el-table-column prop="qty" label="数量" width="110" />
      <el-table-column prop="unit_price" label="单价" width="110" />
      <el-table-column prop="line_total" label="小计" width="120" />
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:12px;gap:16px;">
      <span>应收：¥{{ money(sale.total_amount) }}</span>
      <span>已收：¥{{ money(sale.paid_amount) }}</span>
      <span>未收：¥{{ money(sale.ar_amount) }}</span>
      <el-tag :type="statusTag(sale.payment_status)">{{ statusText(sale.payment_status) }}</el-tag>
    </div>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSaleApi } from '../api/sales'
import { money } from '../utils/format'

const route = useRoute()
const router = useRouter()
const sale = ref(null)

const fmt = (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清' }[v] || '-')
const statusTag = (v) => ({ unpaid: 'danger', partial: 'warning', paid: 'success' }[v] || 'info')

function onPrint() { window.print() }
function onContinue() {
  if (sale.value) {
    localStorage.setItem('shop:new_sale_last', JSON.stringify({ customer_id: sale.value.customer_id, buyer_id: sale.value.buyer_id }))
  }
  router.push('/new-sale')
}
function onProfile() { if (sale.value?.customer_id) router.push(`/customers/${sale.value.customer_id}`) }

onMounted(async () => {
  sale.value = await getSaleApi(Number(route.params.id))
})
</script>
