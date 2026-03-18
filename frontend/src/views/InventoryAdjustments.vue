<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>库存调整</b><el-button type="primary" @click="dialog=true">新增调整</el-button></div></template>

    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <el-select v-model="filters.warehouse_id" clearable placeholder="仓库" style="width:180px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select>
      <el-select v-model="filters.adj_type" clearable placeholder="调整类型" style="width:140px"><el-option label="报溢" value="GAIN" /><el-option label="报损" value="LOSS" /></el-select>
      <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" />
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="rows" border>
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column prop="adj_no" label="调整单号" min-width="160" />
      <el-table-column prop="warehouse_name" label="仓库" width="120" />
      <el-table-column prop="product_name" label="商品" min-width="160" />
      <el-table-column prop="adj_type" label="类型" width="90"><template #default="{row}">{{ row.adj_type === 'GAIN' ? '报溢' : '报损' }}</template></el-table-column>
      <el-table-column prop="qty" label="数量" width="90" />
      <el-table-column prop="reason" label="原因" min-width="140" />
      <el-table-column prop="note" label="备注" min-width="160" />
    </el-table>
  </el-card>

  <el-dialog v-model="dialog" title="新增库存调整" width="560px">
    <el-form label-width="90px">
      <el-form-item label="仓库"><el-select v-model="form.warehouse_id" style="width:220px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
      <el-form-item label="商品"><el-select v-model="form.product_id" filterable style="width:320px"><el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" /></el-select></el-form-item>
      <el-form-item label="类型"><el-radio-group v-model="form.adj_type"><el-radio-button label="GAIN">报溢</el-radio-button><el-radio-button label="LOSS">报损</el-radio-button></el-radio-group></el-form-item>
      <el-form-item label="数量"><el-input-number v-model="form.qty" :min="0.01" /></el-form-item>
      <el-form-item label="原因"><el-input v-model="form.reason" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="submit">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listWarehouses } from '../api/warehouses'
import { listProducts } from '../api/products'
import { createInventoryAdjustment, listInventoryAdjustments } from '../api/inventory_adjustments'

const rows = ref([])
const warehouses = ref([])
const products = ref([])

const filters = reactive({ warehouse_id: null, adj_type: '', dateRange: [] })
const dialog = ref(false)
const form = reactive({ warehouse_id: null, product_id: null, adj_type: 'GAIN', qty: 1, reason: '', note: '' })

async function loadBase() {
  warehouses.value = await listWarehouses({ status: 'ACTIVE' })
  const pRes = await listProducts({ page: 1, page_size: 200, active_only: true })
  products.value = pRes.items || []
}

async function load() {
  rows.value = await listInventoryAdjustments({
    warehouse_id: filters.warehouse_id || undefined,
    adj_type: filters.adj_type || undefined,
    start_date: filters.dateRange?.[0] ? dayjs(filters.dateRange[0]).toISOString() : undefined,
    end_date: filters.dateRange?.[1] ? dayjs(filters.dateRange[1]).toISOString() : undefined,
  })
}

async function submit() {
  try {
    await createInventoryAdjustment({
      warehouse_id: form.warehouse_id,
      product_id: form.product_id,
      adj_type: form.adj_type,
      qty: Number(form.qty || 0),
      reason: form.reason || null,
      note: form.note || null,
    })
    ElMessage.success('库存调整已保存')
    dialog.value = false
    Object.assign(form, { warehouse_id: null, product_id: null, adj_type: 'GAIN', qty: 1, reason: '', note: '' })
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

onMounted(async () => {
  await loadBase()
  await load()
})
</script>
