<template>
  <el-card>
    <template #header><b>操作审计</b></template>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <el-input v-model="filters.actor_name" placeholder="执行人" style="width:180px" clearable />
      <el-input v-model="filters.resource_type" placeholder="资源类型" style="width:180px" clearable />
      <el-input v-model="filters.action" placeholder="动作" style="width:180px" clearable />
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column prop="actor_name" label="执行人" width="120" />
      <el-table-column prop="action" label="动作" width="120" />
      <el-table-column prop="resource_type" label="资源类型" width="120" />
      <el-table-column prop="resource_id" label="资源ID" width="100" />
      <el-table-column prop="detail" label="详情" min-width="240" />
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { listAuditLogs } from '../api/admin'

const rows = ref([])
const filters = reactive({ actor_name: '', resource_type: '', action: '' })

async function load() {
  rows.value = await listAuditLogs({
    actor_name: filters.actor_name || undefined,
    resource_type: filters.resource_type || undefined,
    action: filters.action || undefined,
  })
}

onMounted(load)
</script>
