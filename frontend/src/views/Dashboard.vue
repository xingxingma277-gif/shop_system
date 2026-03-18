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
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="销售总额" :value="kpis.sale_total_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="销售已收" :value="kpis.sale_paid_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="销售应收" :value="kpis.sale_ar_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="库存流水数" :value="kpis.inventory_txn_count || 0" /></el-col>
      </el-row>
      <el-row :gutter="12" style="margin-top:12px;">
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="采购总额" :value="kpis.purchase_total_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="采购应付" :value="kpis.purchase_ap_amount || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="报价单数" :value="kpis.quote_count || 0" /></el-col>
        <el-col :xs="24" :sm="12" :lg="6"><el-statistic title="待交付订单" :value="kpis.delivery_pending_count || 0" /></el-col>
      </el-row>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="8">
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
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header><b>低库存预警</b></template>
          <el-empty v-if="!lowStockItems.length" description="暂无低库存商品" :image-size="80" />
          <div v-else style="display:flex;flex-direction:column;gap:8px;">
            <div v-for="item in lowStockItems" :key="item.id" style="display:flex;justify-content:space-between;gap:12px;font-size:13px;">
              <div>
                <div style="font-weight:600;">{{ item.name }}</div>
                <div style="color:#909399;">{{ item.sku || '无 SKU' }}</div>
              </div>
              <div style="text-align:right;">
                <div>库存：{{ item.stock_quantity }}</div>
                <div style="color:#E6A23C;">预警：{{ item.stock_warning_threshold }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
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

    <el-card shadow="never">
      <template #header><b>最近操作</b></template>
      <el-table :data="recentAudits" border>
        <el-table-column prop="created_at" label="时间" min-width="170" />
        <el-table-column prop="actor_name" label="操作人" width="120" />
        <el-table-column prop="action" label="动作" width="160" />
        <el-table-column prop="resource_type" label="资源" width="140" />
        <el-table-column prop="detail" label="详情" min-width="260" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboardSummary } from '../api/reports'
import { hasPermission } from '../utils/auth'

const router = useRouter()
const kpis = reactive({ sale_total_amount: 0, sale_paid_amount: 0, sale_ar_amount: 0, inventory_txn_count: 0, purchase_total_amount: 0, purchase_ap_amount: 0, quote_count: 0, delivery_pending_count: 0 })
const agingSummary = reactive({ '0_30': 0, '31_60': 0, '61_90': 0, '90_plus': 0 })
const lowStockItems = ref([])
const recentAudits = ref([])

async function loadDashboard() {
  const data = await getDashboardSummary({})
  Object.assign(kpis, data.kpis || {})
  Object.assign(agingSummary, data.ap_aging || {})
  lowStockItems.value = data.low_stock_items || []
  recentAudits.value = data.recent_audits || []
}

onMounted(loadDashboard)
</script>
