<template>
  <el-card shadow="never" class="mb-12">
    <template #header>
      <div class="card-header">
        <div style="font-weight:700;">新建拿货单</div>
        <el-button type="primary" :loading="saving" @click="submit">保存单据</el-button>
      </div>
    </template>

    <el-form :model="form" label-width="84px">
      <el-form-item label="客户" required>
        <el-select v-model="form.customer_id" filterable remote clearable :remote-method="onSearchCustomers" style="width: 320px" @change="onCustomerChanged">
          <el-option v-for="c in catalog.customers" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="拿货人" required>
        <el-select v-model="form.buyer_id" filterable clearable style="width:320px">
          <el-option v-for="b in buyers" :key="b.id" :label="b.name" :value="b.id" :disabled="!b.is_active" />
        </el-select>
        <el-button style="margin-left:8px" @click="openBuyerDialog" :disabled="!form.customer_id">新增拿货人</el-button>
      </el-form-item>

      <el-form-item label="项目" required>
        <el-input v-model="form.project" placeholder="请输入开单项目" style="width:320px" />
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.note" />
      </el-form-item>
    </el-form>
  </el-card>

  <el-card shadow="never">
    <template #header>
      <div class="card-header"><div style="font-weight:700;">商品明细</div><el-button @click="addRow">添加一行</el-button></div>
    </template>

    <el-table :data="items" border>
      <el-table-column label="商品" min-width="260">
        <template #default="{ row }">
          <el-select v-model="row.product_id" filterable remote clearable :remote-method="onSearchProducts" style="width:100%" @change="()=>onProductChanged(row)">
            <el-option v-for="p in catalog.products" :key="p.id" :label="p.name" :value="p.id" :disabled="!p.is_active" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="数量" width="140">
        <template #default="{ row }"><el-input-number v-model="row.qty" :min="0.01" /></template>
      </el-table-column>
      <el-table-column label="单价" width="220">
        <template #default="{ row }">
          <el-input-number v-model="row.unit_price" :min="0" />
          <el-button circle plain :disabled="!canQueryPricing(row)" @click="ensureHistory(row)">¥</el-button>
        </template>
      </el-table-column>
      <el-table-column label="小计" width="120">
        <template #default="{ row }">{{ money((row.qty || 0) * (row.unit_price || 0)) }}</template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="buyerDialog" title="新增拿货人" width="420px">
    <el-form label-width="80px"><el-form-item label="姓名"><el-input v-model="buyerForm.name" /></el-form-item></el-form>
    <template #footer><el-button @click="buyerDialog=false">取消</el-button><el-button type="primary" @click="submitBuyer">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCatalogStore } from '../stores/catalog'
import { createBuyer, getCustomerProductPriceHistory, listBuyers } from '../api/customers'
import { getLastPricing } from '../api/pricing'
import { createSale } from '../api/sales'
import { money } from '../utils/format'

const router = useRouter()
const catalog = useCatalogStore()

const form = reactive({ customer_id: null, buyer_id: null, project: '', note: '' })
const buyers = ref([])
const saving = ref(false)
const buyerDialog = ref(false)
const buyerForm = reactive({ name: '' })

const items = ref([{ _key: 1, product_id: null, qty: 1, unit_price: 0, history: [] }])

const onSearchCustomers = (q) => catalog.searchCustomers(q || '')
const onSearchProducts = (q) => catalog.searchProducts(q || '')

async function onCustomerChanged() {
  if (!form.customer_id) return
  buyers.value = await listBuyers(form.customer_id)
  form.buyer_id = buyers.value[0]?.id || null
}

async function onProductChanged(row) {
  if (!row.product_id) return
  const p = catalog.products.find((x) => x.id === row.product_id)
  row.unit_price = Number(p?.standard_price || 0)
  if (canQueryPricing(row)) {
    const last = await getLastPricing({ customer_id: form.customer_id, product_id: row.product_id })
    if (last?.found) row.unit_price = Number(last.last_price)
  }
}

function canQueryPricing(row) {
  return !!form.customer_id && !!row.product_id
}

async function ensureHistory(row) {
  row.history = await getCustomerProductPriceHistory(form.customer_id, row.product_id, 20).then((r) => r.items || [])
  ElMessage.info(`历史记录 ${row.history.length} 条，可在后续版本图表弹窗展示`)
}

function addRow() {
  items.value.push({ _key: Date.now(), product_id: null, qty: 1, unit_price: 0, history: [] })
}

function openBuyerDialog() {
  buyerDialog.value = true
}

async function submitBuyer() {
  if (!form.customer_id || !buyerForm.name.trim()) return
  const b = await createBuyer(form.customer_id, { name: buyerForm.name })
  buyers.value.unshift(b)
  form.buyer_id = b.id
  buyerForm.name = ''
  buyerDialog.value = false
}

async function submit() {
  if (!form.customer_id || !form.buyer_id || !form.project.trim()) {
    ElMessage.warning('客户/拿货人/项目为必填')
    return
  }
  const validItems = items.value
    .filter((r) => r.product_id && Number(r.qty) > 0)
    .map((r) => ({ product_id: r.product_id, qty: Number(r.qty), unit_price: Number(r.unit_price || 0), note: null }))
  if (!validItems.length) {
    ElMessage.warning('请至少添加 1 行商品')
    return
  }

  saving.value = true
  try {
    const sale = await createSale({ customer_id: form.customer_id, buyer_id: form.buyer_id, project: form.project, note: form.note || null, items: validItems })
    router.push(`/sales/${sale.id}/checkout`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await catalog.searchCustomers('')
  await catalog.searchProducts('')
})
</script>
