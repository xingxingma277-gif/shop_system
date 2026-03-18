<template>
  <el-container class="app-shell">
    <el-aside width="220px" class="aside">
      <div class="logo">进销存 · 拿货开单</div>

      <el-menu :default-active="route.path" router>
        <el-menu-item index="/new-sale">
          <el-icon><DocumentAdd /></el-icon>
          <span>开单</span>
        </el-menu-item>

        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <span>商品管理</span>
        </el-menu-item>

        <el-menu-item index="/customers">
          <el-icon><User /></el-icon>
          <span>客户管理</span>
        </el-menu-item>

        <el-menu-item index="/suppliers">
          <el-icon><User /></el-icon>
          <span>供应商管理</span>
        </el-menu-item>

        <el-menu-item index="/warehouses">
          <el-icon><OfficeBuilding /></el-icon>
          <span>仓库管理</span>
        </el-menu-item>

        <el-sub-menu index="inventory-group">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>采购与库存</span>
          </template>
          <el-menu-item index="/purchases">采购管理</el-menu-item>
          <el-menu-item index="/inventory-ledger">库存台账</el-menu-item>
          <el-menu-item index="/inventory-checks">库存盘点</el-menu-item>
          <el-menu-item index="/inventory-transfers">库存调拨</el-menu-item>
          <el-menu-item index="/inventory-adjustments">库存调整</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/accounts-payable">
          <el-icon><CreditCard /></el-icon>
          <span>应付管理</span>
        </el-menu-item>

        <el-menu-item index="/reports">
          <el-icon><PieChart /></el-icon>
          <span>经营报表</span>
        </el-menu-item>

        <el-sub-menu index="admin-group">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>权限与审计</span>
          </template>
          <el-menu-item index="/admin/users">用户与角色</el-menu-item>
          <el-menu-item index="/admin/audit-logs">操作审计</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/transactions">
          <el-icon><DataAnalysis /></el-icon>
          <span>交易记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div style="font-weight:700;">{{ route.meta.title || '进销存' }}</div>
        <el-tag type="info" effect="plain">本地单机版</el-tag>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Box, CreditCard, DataAnalysis, DocumentAdd, Goods, OfficeBuilding, PieChart, Setting, User } from '@element-plus/icons-vue'

const route = useRoute()
</script>
