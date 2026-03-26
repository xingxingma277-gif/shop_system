<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside-menu">
      <div class="logo-area">
        <h1 class="logo-text">企业进销存系统</h1>
      </div>
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" style="border-right: none;">
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon><span>经营看板</span>
        </el-menu-item>

        <el-sub-menu index="sales_group">
          <template #title><el-icon><ShoppingCart /></el-icon><span>销售与客户</span></template>
          <el-menu-item index="/sales/wizard">开单</el-menu-item>
          <el-menu-item index="/transactions">交易记录</el-menu-item>
          <el-menu-item index="/customers">客户档案</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="purchase_group">
          <template #title><el-icon><Van /></el-icon><span>采购与供应商</span></template>
          <el-menu-item index="/purchases">采购单据</el-menu-item>
          <el-menu-item index="/suppliers">供应商档案</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="inventory_group">
          <template #title><el-icon><Box /></el-icon><span>仓储与库存</span></template>
          <el-menu-item index="/inventory-ledger">库存台账</el-menu-item>
          <el-menu-item index="/inventory-checks">库存盘点</el-menu-item>
          <el-menu-item index="/inventory-transfers">库存调拨</el-menu-item>
          <el-menu-item index="/inventory-adjustments">库存调整</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="master_data_group">
          <template #title><el-icon><Collection /></el-icon><span>基础资料</span></template>
          <el-menu-item index="/products">商品管理</el-menu-item>
          <el-menu-item index="/warehouses">仓库设置</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="system_group">
          <template #title><el-icon><Setting /></el-icon><span>系统与权限</span></template>
          <el-menu-item index="/admin/users">账号与审计</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="top-header">
        <span class="page-current-title">{{ route.meta.title || '系统管理' }}</span>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Odometer, ShoppingCart, Van, Box, Collection, Setting } from '@element-plus/icons-vue'
const route = useRoute()
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside-menu { background-color: #304156; display: flex; flex-direction: column; }
.logo-area { height: 60px; display: flex; align-items: center; justify-content: center; background-color: #2b3643; }
.logo-text { color: #fff; font-size: 18px; font-weight: bold; margin: 0; }
.top-header { background-color: #fff; box-shadow: 0 1px 4px rgba(0,21,41,0.08); display: flex; align-items: center; }
.page-current-title { font-size: 16px; font-weight: 500; color: #606266; }
.main-content { background-color: #f0f2f5; padding: 16px; }
</style>