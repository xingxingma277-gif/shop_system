<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="aside">
      <div class="logo">进销存 · 拿货开单</div>

      <el-menu :default-active="route.path" router>
        <el-menu-item v-if="can('report.view')" index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>经营看板</span>
        </el-menu-item>

        <el-menu-item v-if="can('sale.manage')" index="/new-sale">
          <el-icon><DocumentAdd /></el-icon>
          <span>开单</span>
        </el-menu-item>

        <el-menu-item v-if="can('product.manage')" index="/products">
          <el-icon><Goods /></el-icon>
          <span>商品管理</span>
        </el-menu-item>

        <el-menu-item v-if="can('customer.manage')" index="/customers">
          <el-icon><User /></el-icon>
          <span>客户管理</span>
        </el-menu-item>

        <el-menu-item v-if="can('purchase.manage')" index="/suppliers">
          <el-icon><User /></el-icon>
          <span>供应商管理</span>
        </el-menu-item>

        <el-menu-item v-if="can('inventory.manage')" index="/warehouses">
          <el-icon><OfficeBuilding /></el-icon>
          <span>仓库管理</span>
        </el-menu-item>

        <el-sub-menu v-if="canAny(['purchase.manage', 'inventory.view', 'inventory.manage'])" index="inventory-group">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>采购与库存</span>
          </template>
          <el-menu-item v-if="can('purchase.manage')" index="/purchases">采购管理</el-menu-item>
          <el-menu-item v-if="can('inventory.view')" index="/inventory-ledger">库存台账</el-menu-item>
          <el-menu-item v-if="can('inventory.manage')" index="/inventory-checks">库存盘点</el-menu-item>
          <el-menu-item v-if="can('inventory.manage')" index="/inventory-transfers">库存调拨</el-menu-item>
          <el-menu-item v-if="can('inventory.manage')" index="/inventory-adjustments">库存调整</el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="can('purchase.manage')" index="/accounts-payable">
          <el-icon><CreditCard /></el-icon>
          <span>应付管理</span>
        </el-menu-item>

        <el-menu-item v-if="can('report.view')" index="/reports">
          <el-icon><PieChart /></el-icon>
          <span>经营报表</span>
        </el-menu-item>

        <el-sub-menu v-if="canAny(['admin.user.manage', 'audit.view'])" index="admin-group">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>权限与审计</span>
          </template>
          <el-menu-item v-if="can('admin.user.manage')" index="/admin/users">用户与角色</el-menu-item>
          <el-menu-item v-if="can('audit.view')" index="/admin/audit-logs">操作审计</el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="can('transaction.view')" index="/transactions">
          <el-icon><DataAnalysis /></el-icon>
          <span>交易记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div style="font-weight:700;">{{ route.meta.title || '进销存' }}</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <el-tag type="info" effect="plain">本地单机版</el-tag>
          <el-tag v-if="authDisplayName" type="success" effect="plain">{{ authDisplayName }}</el-tag>
          <el-button v-if="authDisplayName" link type="danger" @click="logout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { logout as logoutRequest } from './api/auth'
import { Box, CreditCard, DataAnalysis, DocumentAdd, Goods, Odometer, OfficeBuilding, PieChart, Setting, User } from '@element-plus/icons-vue'
import { clearStoredAuth, getStoredAuth, hasPermission } from './utils/auth'

const route = useRoute()
const auth = computed(() => getStoredAuth() || {})
const authDisplayName = computed(() => auth.value?.display_name || localStorage.getItem('shop:auth_display_name'))

function can(code) {
  return hasPermission(code)
}

function canAny(codes) {
  return (codes || []).some(code => can(code))
}

async function logout() {
  try { await logoutRequest() } catch (e) {}
  clearStoredAuth()
  window.location.href = '/login'
}
</script>
