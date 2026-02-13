<template>
  <div>
    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="12">
        <el-card>
          <template #header>客户信息</template>
          <div><b>{{ customer?.name }}</b>（{{ customer?.type }}）</div>
          <div>联系人：{{ customer?.contact_name || '-' }}</div>
          <div>电话：{{ customer?.phone || '-' }}</div>
          <div>地址：{{ customer?.address || '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>欠款概览</template>
          <div>累计销售：¥{{ ar.total_sales.toFixed(2) }}</div>
          <div>累计已收：¥{{ ar.total_received.toFixed(2) }}</div>
          <div>累计欠款：<b style="color:#d4380d">¥{{ ar.total_ar.toFixed(2) }}</b></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <el-tabs v-model="tab" @tab-change="onTab">
        <el-tab-pane label="公司总账单" name="statement">
          <el-table :data="statement.items" border>
            <el-table-column prop="sale_id" label="单号" width="100" />
            <el-table-column prop="date" label="日期" width="180" />
            <el-table-column prop="project" label="项目" />
            <el-table-column prop="buyer_name" label="拿货人" width="120" />
            <el-table-column prop="total" label="总额" width="100" />
            <el-table-column prop="paid" label="已付" width="100" />
            <el-table-column prop="ar" label="未付" width="100" />
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="按拿货人账单" name="buyer">
          <el-select v-model="buyerId" placeholder="选择拿货人" style="width:260px;margin-bottom:10px" @change="loadBuyerStatement">
            <el-option v-for="b in buyers" :key="b.id" :value="b.id" :label="b.name" />
          </el-select>
          <el-table :data="buyerStatement.items" border>
            <el-table-column prop="sale_id" label="单号" width="100" />
            <el-table-column prop="date" label="日期" width="180" />
            <el-table-column prop="project" label="项目" />
            <el-table-column prop="total" label="总额" width="100" />
            <el-table-column prop="paid" label="已付" width="100" />
            <el-table-column prop="ar" label="未付" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api/http'
import { getCustomer, listBuyers } from '../api/customers'
import { getCustomerArSummary, getCustomerStatement } from '../api/customers_ext'

const route = useRoute()
const customerId = Number(route.params.id)

const tab = ref('statement')
const customer = ref(null)
const buyers = ref([])
const buyerId = ref(null)

const ar = reactive({ total_sales: 0, total_received: 0, total_ar: 0 })
const statement = reactive({ items: [] })
const buyerStatement = reactive({ items: [] })

async function loadBase() {
  const rs = await Promise.allSettled([
    getCustomer(customerId),
    getCustomerArSummary(customerId),
    getCustomerStatement(customerId, { page: 1, page_size: 50 }),
    listBuyers(customerId),
  ])
  if (rs[0].status === 'fulfilled') customer.value = rs[0].value
  if (rs[1].status === 'fulfilled') Object.assign(ar, rs[1].value)
  if (rs[2].status === 'fulfilled') statement.items = rs[2].value.items || []
  if (rs[3].status === 'fulfilled') {
    buyers.value = rs[3].value || []
    buyerId.value = buyers.value[0]?.id || null
  }
}

async function loadBuyerStatement() {
  if (!buyerId.value) return
  const data = await http.get(`/api/buyers/${buyerId.value}/statement`, { params: { page: 1, page_size: 50 } }).then((r) => r.data)
  buyerStatement.items = data.items || []
}

function onTab() {
  if (tab.value === 'buyer') loadBuyerStatement().catch(() => ElMessage.error('拿货人账单加载失败'))
}

onMounted(async () => {
  try {
    await loadBase()
  } catch {
    ElMessage.error('客户档案加载失败')
  }
})
</script>
