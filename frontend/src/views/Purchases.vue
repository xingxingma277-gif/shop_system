<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>采购管理</b><el-button type="primary" @click="openCreate">新建采购单</el-button></div></template>
    <div style="display:flex;gap:8px;margin-bottom:10px;">
      <el-select v-model="filters.supplier_id" clearable filterable placeholder="供应商" style="width:220px"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select>
      <el-select v-model="filters.status" clearable placeholder="状态" style="width:160px"><el-option label="草稿" value="DRAFT" /><el-option label="已确认" value="CONFIRMED" /><el-option label="部分入库" value="RECEIVED_PARTIAL" /><el-option label="已入库" value="RECEIVED" /></el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="purchase_no" label="采购单号" min-width="150" />
      <el-table-column prop="supplier_name" label="供应商" min-width="140" />
      <el-table-column prop="warehouse_name" label="仓库" min-width="120" />
      <el-table-column prop="total_amount" label="总金额" width="100" />
      <el-table-column prop="ap_amount" label="应付" width="100" />
      <el-table-column prop="status" label="状态" width="130" />
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button link type="primary" @click="confirmRow(row)" :disabled="row.status!=='DRAFT'">确认</el-button>
          <el-button link type="success" @click="openReceive(row)" :disabled="!['CONFIRMED','RECEIVED_PARTIAL'].includes(row.status)">入库</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="createDialog" title="新建采购单" width="760px">
    <el-form label-width="90px">
      <el-form-item label="供应商"><el-select v-model="createForm.supplier_id" style="width:240px"><el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item>
      <el-form-item label="仓库"><el-select v-model="createForm.warehouse_id" style="width:240px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select></el-form-item>
    </el-form>
    <el-table :data="createForm.items" border>
      <el-table-column label="商品" min-width="220"><template #default="{row}"><el-select v-model="row.product_id" filterable><el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" /></el-select></template></el-table-column>
      <el-table-column label="数量" width="120"><template #default="{row}"><el-input-number v-model="row.qty" :min="0.01" /></template></el-table-column>
      <el-table-column label="单价" width="120"><template #default="{row}"><el-input-number v-model="row.unit_cost" :min="0" /></template></el-table-column>
      <el-table-column width="90"><template #default="{$index}"><el-button link type="danger" @click="createForm.items.splice($index,1)">删除</el-button></template></el-table-column>
    </el-table>
    <div style="margin-top:8px;"><el-button @click="createForm.items.push({ product_id:null, qty:1, unit_cost:0 })">+ 添加行</el-button></div>
    <template #footer><el-button @click="createDialog=false">取消</el-button><el-button type="primary" @click="submitCreate">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="receiveDialog" title="采购入库" width="720px">
    <el-table :data="receiveRows" border>
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="qty" label="采购数量" width="110" />
      <el-table-column prop="received_qty" label="已入库" width="110" />
      <el-table-column label="本次入库" width="160"><template #default="{row}"><el-input-number v-model="row.receive_qty" :min="0" :max="Math.max(0, row.qty-row.received_qty)" /></template></el-table-column>
    </el-table>
    <template #footer><el-button @click="receiveDialog=false">取消</el-button><el-button type="primary" @click="submitReceive">确认入库</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listSuppliers } from '../api/suppliers'
import { listWarehouses } from '../api/warehouses'
import { listProducts } from '../api/products'
import { confirmPurchase, createPurchase, getPurchase, listPurchases, receivePurchase } from '../api/purchases'

const suppliers = ref([])
const warehouses = ref([])
const products = ref([])
const rows = ref([])
const filters = reactive({ supplier_id: null, status: '' })

const createDialog = ref(false)
const createForm = reactive({ supplier_id: null, warehouse_id: null, items: [{ product_id: null, qty: 1, unit_cost: 0 }] })

const receiveDialog = ref(false)
const receivePurchaseId = ref(null)
const receiveRows = ref([])

async function loadBase() {
  suppliers.value = await listSuppliers({ status: 'ACTIVE' })
  warehouses.value = await listWarehouses({ status: 'ACTIVE' })
  const pRes = await listProducts({ page: 1, page_size: 200, active_only: true })
  products.value = pRes.items || []
}

async function load() {
  rows.value = await listPurchases({ supplier_id: filters.supplier_id || undefined, status: filters.status || undefined })
}

function openCreate() {
  createDialog.value = true
}

async function submitCreate() {
  try {
    await createPurchase({
      supplier_id: createForm.supplier_id,
      warehouse_id: createForm.warehouse_id,
      items: createForm.items.filter(i => i.product_id).map(i => ({ product_id: i.product_id, qty: Number(i.qty || 0), unit_cost: Number(i.unit_cost || 0) }))
    })
    ElMessage.success('采购单已创建')
    createDialog.value = false
    createForm.supplier_id = null
    createForm.warehouse_id = null
    createForm.items = [{ product_id: null, qty: 1, unit_cost: 0 }]
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  }
}

async function confirmRow(row) {
  try {
    await confirmPurchase(row.id)
    ElMessage.success('采购单已确认')
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  }
}

async function openReceive(row) {
  const detail = await getPurchase(row.id)
  receivePurchaseId.value = row.id
  receiveRows.value = (detail.items || []).map(it => ({ ...it, receive_qty: Math.max(0, Number(it.qty) - Number(it.received_qty)) }))
  receiveDialog.value = true
}

async function submitReceive() {
  try {
    await receivePurchase(receivePurchaseId.value, {
      items: receiveRows.value.filter(r => Number(r.receive_qty) > 0).map(r => ({ purchase_item_id: r.id, receive_qty: Number(r.receive_qty) }))
    })
    ElMessage.success('入库成功')
    receiveDialog.value = false
    await load()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '入库失败')
  }
}

onMounted(async () => {
  await loadBase()
  await load()
})
</script>
