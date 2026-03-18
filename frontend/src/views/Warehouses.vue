<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>仓库管理</b><el-button type="primary" @click="dialog=true">新增仓库</el-button></div></template>
    <el-table :data="rows" border>
      <el-table-column prop="code" label="编码" width="130" />
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="address" label="地址" min-width="220" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="默认" width="90"><template #default="{row}">{{ row.is_default ? '是' : '否' }}</template></el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialog" title="新增仓库" width="420px">
    <el-form label-width="90px">
      <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
      <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
      <el-form-item label="默认仓库"><el-switch v-model="form.is_default" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createWarehouse, listWarehouses } from '../api/warehouses'

const rows = ref([])
const dialog = ref(false)
const form = reactive({ code: '', name: '', address: '', is_default: false })

async function load() {
  rows.value = await listWarehouses({})
}

async function submit() {
  try {
    await createWarehouse(form)
    ElMessage.success('仓库已创建')
    dialog.value = false
    Object.assign(form, { code: '', name: '', address: '', is_default: false })
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

onMounted(load)
</script>
