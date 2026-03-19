<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>供应商管理</b><el-button type="primary" @click="dialog=true">新增供应商</el-button></div></template>
    <div style="display:flex;gap:8px;margin-bottom:10px;">
      <el-input v-model="q" placeholder="编码/名称" style="width:240px" clearable />
      <el-select v-model="status" clearable placeholder="状态" style="width:140px"><el-option label="启用" value="ACTIVE" /><el-option label="停用" value="INACTIVE" /></el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="contact_name" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="status" label="状态" width="110" />
    </el-table>
  </el-card>

  <el-dialog v-model="dialog" title="新增供应商" width="500px">
    <el-form label-width="90px">
      <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
      <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="联系人"><el-input v-model="form.contact_name" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
      <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createSupplier, listSuppliers } from '../api/suppliers'

const rows = ref([])
const q = ref('')
const status = ref('')
const dialog = ref(false)
const form = reactive({ code: '', name: '', contact_name: '', phone: '', address: '', note: '' })

async function load() {
  rows.value = await listSuppliers({ q: q.value || undefined, status: status.value || undefined })
}

async function submit() {
  try {
    await createSupplier(form)
    ElMessage.success('供应商已创建')
    dialog.value = false
    Object.assign(form, { code: '', name: '', contact_name: '', phone: '', address: '', note: '' })
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

onMounted(load)
</script>
