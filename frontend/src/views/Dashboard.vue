<template>
  <div style="display:flex;flex-direction:column;gap:16px;">
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
          <b>经营看板</b>
          <div style="color:#909399;font-size:13px;">基于已登录用户可访问的报表数据生成</div>
        </div>
      </template>

      <el-row :gutter="12">
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="采购总额" :value="apSummary.total_purchase_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="已付金额" :value="apSummary.total_paid_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="应付余额" :value="apSummary.total_ap_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="库存流水数" :value="invSummary.count || 0" /></el-col>
      </el-row>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never">
          <template #header><b>AP 账龄</b></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="0-30 天">{{ agingSummary['0_30'] || 0 }}</el-descriptions-item>
            <el-descriptions-item label="31-60 天">{{ agingSummary['31_60'] || 0 }}</el-descriptions-item>
            <el-descriptions-item label="61-90 天">{{ agingSummary['61_90'] || 0 }}</el-descriptions-item>
            <el-descriptions-item label="90+ 天">{{ agingSummary['90_plus'] || 0 }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:12px;display:flex;justify-content:flex-end;">
            <el-button type="primary" link @click="router.push('/reports')">查看完整报表</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never">
          <template #header><b>快捷入口</b></template>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <el-button v-if="hasPermission('purchase.view')" @click="router.push('/purchases')">采购管理</el-button>
            <el-button v-if="hasPermission('inventory.view')" @click="router.push('/inventory-ledger')">库存台账</el-button>
            <el-button v-if="hasPermission('sale.view')" @click="router.push('/transactions')">交易记录</el-button>
            <el-button v-if="hasPermission('admin.user.manage')" @click="router.push('/admin/users')">用户与角色</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { getApAging, getApSummary, getInventorySummary } from '../api/reports'
import { hasPermission } from '../utils/auth'

const router = useRouter()
const apSummary = reactive({ total_purchase_amount: 0, total_paid_amount: 0, total_ap_amount: 0 })
const invSummary = reactive({ in_qty: 0, out_qty: 0, count: 0 })
const agingSummary = reactive({ '0_30': 0, '31_60': 0, '61_90': 0, '90_plus': 0 })

async function loadDashboard() {
  const [ap, aging, inventory] = await Promise.all([
    getApSummary({}),
    getApAging({}),
    getInventorySummary({}),
  ])
  Object.assign(apSummary, ap.summary || {})
  Object.assign(agingSummary, aging.summary || {})
  Object.assign(invSummary, inventory.summary || {})
}

onMounted(loadDashboard)
</script>
