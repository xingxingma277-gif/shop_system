<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>库存调拨</b><el-button type="primary" @click="dialog=true">新建调拨</el-button></div></template>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <el-select v-model="filters.warehouse_id" clearable placeholder="仓库" style="width:180px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select>
      <el-select v-model="filters.status" clearable placeholder="状态" style="width:160px"><el-option label="草稿" value="DRAFT" /><el-option label="已过账" value="POSTED" /></el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="transfer_no" label="调拨单号" min-width="160" />
      <el-table-column prop="from_warehouse_name" label="调出仓" width="120" />
      <el-table-column prop="to_warehouse_name" label="调入仓" width="120" />
      <el-table-column prop="product_name" label="商品" min-width="160" />
      <el-table-column prop="qty" label="数量" width="100" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="row.status !== 'DRAFT'" @click="submitPost(row)">过账</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialog" title="新建调拨" width="520px">
    <el-form label-width="100px">
      <el-form-item label="调出仓库"><el-select v-model="form.from_warehouse_id" style="width:240px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="调入仓库"><el-select v-model="form.to_warehouse_id" style="width:240px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="商品"><el-select v-model="form.product_id" filterable style="width:240px"><el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" /></el-select></el-form-item>
      <el-form-item label="数量"><el-input-number v-model="form.qty" :min="0.01" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="submitCreate">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listProducts } from '../api/products'
import { createInventoryTransfer, listInventoryTransfers, postInventoryTransfer } from '../api/inventory'
import { listWarehouses } from '../api/warehouses'

const rows = ref([])
const warehouses = ref([])
const products = ref([])
const filters = reactive({ warehouse_id: null, status: '' })
const dialog = ref(false)
const form = reactive({ from_warehouse_id: null, to_warehouse_id: null, product_id: null, qty: 1, note: '' })

async function loadBase() {
  warehouses.value = await listWarehouses({ status: 'ACTIVE' })
  const res = await listProducts({ page: 1, page_size: 200, active_only: true })
  products.value = res.items || []
}

async function load() {
  rows.value = await listInventoryTransfers({ warehouse_id: filters.warehouse_id || undefined, status: filters.status || undefined })
}

async function submitCreate() {
  try {
    await createInventoryTransfer({ ...form, qty: Number(form.qty || 0) })
    dialog.value = false
    form.from_warehouse_id = null
    form.to_warehouse_id = null
    form.product_id = null
    form.qty = 1
    form.note = ''
    ElMessage.success('调拨单已创建')
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  }
}

async function submitPost(row) {
  try {
    await postInventoryTransfer(row.id)
    ElMessage.success('调拨单已过账')
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '过账失败')
  }
}

onMounted(async () => {
  await loadBase()
  await load()
})
</script>
