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
import { DocumentAdd, Goods, User } from '@element-plus/icons-vue'

const route = useRoute()
</script>
