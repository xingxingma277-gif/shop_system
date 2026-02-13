<template>
  <el-card shadow="never" class="mb-12">
    <template #header>
      <div class="card-header">
        <div style="font-weight:700;">新建拿货单</div>
        <el-button type="primary" :loading="saving" @click="submit">保存单据</el-button>
      </div>
    </template>

    <el-form :model="form" label-width="84px">
      <el-form-item label="订单编号"><el-input v-model="form.sale_no" readonly style="width:320px" /></el-form-item>
      <el-form-item label="客户" required>
        <el-select v-model="form.customer_id" filterable remote clearable :remote-method="onSearchCustomers" style="width: 320px" @change="onCustomerChanged">
          <el-option v-for="c in catalog.customers" :key="c.id" :label="`${c.name}${c.is_active ? '' : '（已停用）'}`" :value="c.id" :disabled="!c.is_active" />
        </el-select>
      </el-form-item>
      <el-form-item label="拿货人" required v-if="showBuyer">
        <el-select v-model="form.buyer_id" filterable clearable style="width:320px">
          <el-option v-for="b in buyers" :key="b.id" :label="b.name" :value="b.id" :disabled="!b.is_active" />
        </el-select>
        <el-button style="margin-left:8px" @click="openBuyerDialog" :disabled="!form.customer_id">新增拿货人</el-button>
      </el-form-item>
      <el-form-item label="项目"><el-input v-model="form.project" placeholder="可选" style="width:320px" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
    </el-form>
  </el-card>

  <el-card shadow="never">
    <template #header><div class="card-header"><div style="font-weight:700;">商品明细</div><el-button @click="addRow">添加一行</el-button></div></template>
    <el-table :data="items" border>
      <el-table-column label="商品" min-width="260">
        <template #default="{ row }">
          <el-select v-model="row.product_id" filterable remote clearable :remote-method="onSearchProducts" style="width:100%" @change="()=>onProductChanged(row)">
            <el-option v-for="p in catalog.products" :key="p.id" :label="`${p.name}${p.is_active ? '' : '（已停售）'}`" :value="p.id" :disabled="!p.is_active" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="数量" width="140"><template #default="{ row }"><el-input-number v-model="row.qty" :min="0.01" /></template></el-table-column>
      <el-table-column label="单价" width="380">
        <template #default="{ row }">
          <el-input-number v-model="row.unit_price" :min="0" />
          <el-button v-if="row.lastPrice != null" size="small" type="success" plain style="margin-left:8px" @click="applyLastPrice(row)">用上次价格</el-button>
          <el-tooltip content="查看历史拿价" placement="top">
            <el-button circle plain size="large" :disabled="!canQueryPricing(row)" style="margin-left:8px" @click="openHistory(row)"><el-icon><Clock /></el-icon></el-button>
          </el-tooltip>
          <el-tag v-if="row.lastPrice != null" type="warning" style="margin-left:8px">上次拿价：¥{{ money(row.lastPrice) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="小计" width="120"><template #default="{ row }">{{ money((row.qty || 0) * (row.unit_price || 0)) }}</template></el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="historyDialog" title="历史拿价" width="760px">
    <el-table :data="historyRows" border size="small">
      <el-table-column prop="date" label="时间" min-width="160"><template #default="{row}">{{ fmt(row.date) }}</template></el-table-column>
      <el-table-column prop="sale_no" label="单号" min-width="160" />
      <el-table-column prop="unit_price" label="单价" width="110" />
      <el-table-column prop="qty" label="数量" width="100" />
      <el-table-column prop="project" label="项目" min-width="140" />
      <el-table-column prop="note" label="备注" min-width="140" show-overflow-tooltip />
    </el-table>
    <div style="margin-top:8px;color:#666">共 {{ historyMeta.total }} 条</div>
  </el-dialog>

  <el-dialog v-model="buyerDialog" title="新增拿货人" width="420px">
    <el-form label-width="80px"><el-form-item label="姓名"><el-input v-model="buyerForm.name" /></el-form-item></el-form>
    <template #footer><el-button @click="buyerDialog=false">取消</el-button><el-button type="primary" @click="submitBuyer">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import dayjs from 'dayjs'
import { Clock } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCatalogStore } from '../stores/catalog'
import { createBuyer, getCustomerProductPriceHistory, listBuyers } from '../api/customers'
import { getLastPricing } from '../api/pricing'
import { createSale, getNextSaleNo } from '../api/sales'
import { money } from '../utils/format'

const router = useRouter()
const catalog = useCatalogStore()
const form = reactive({ sale_no: '', customer_id: null, buyer_id: null, project: '', note: '' })
const buyers = ref([])
const saving = ref(false)
const buyerDialog = ref(false)
const buyerForm = reactive({ name: '' })
const items = ref([{ _key: 1, product_id: null, qty: 1, unit_price: 0, history: [], lastPrice: null }])
const historyDialog = ref(false)
const historyRows = ref([])
const historyMeta = reactive({ total: 0 })

const showBuyer = computed(() => (catalog.customers.find((x) => x.id === form.customer_id)?.type !== 'personal'))
const onSearchCustomers = (q) => catalog.searchCustomers(q || '')
const onSearchProducts = (q) => catalog.searchProducts(q || '')
const fmt = (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-')

async function onCustomerChanged() {
  if (!form.customer_id) return
  buyers.value = await listBuyers(form.customer_id)
  const c = catalog.customers.find((x) => x.id === form.customer_id)
  form.buyer_id = c?.type === 'personal' ? null : buyers.value[0]?.id || null
}

async function onProductChanged(row) {
  if (!row.product_id) return
  row.unit_price = Number(catalog.products.find((x) => x.id === row.product_id)?.standard_price || 0)
  if (canQueryPricing(row)) {
    const last = await getLastPricing({ customer_id: form.customer_id, product_id: row.product_id })
    row.lastPrice = last?.found ? Number(last.last_price) : null
  }
}

function canQueryPricing(row) {
  return !!form.customer_id && !!row.product_id
}

function applyLastPrice(row) {
  if (row.lastPrice != null) row.unit_price = Number(row.lastPrice)
}

async function openHistory(row) {
  if (!canQueryPricing(row)) return
  const res = await getCustomerProductPriceHistory(form.customer_id, row.product_id, { page: 1, page_size: 20 })
  historyRows.value = res.items || []
  historyMeta.total = res.meta?.total || 0
  row.history = historyRows.value
  historyDialog.value = true
}

function addRow() {
  items.value.push({ _key: Date.now(), product_id: null, qty: 1, unit_price: 0, history: [], lastPrice: null })
}
function openBuyerDialog() { buyerDialog.value = true }

async function submitBuyer() {
  if (!form.customer_id || !buyerForm.name.trim()) return
  const b = await createBuyer(form.customer_id, { name: buyerForm.name })
  buyers.value.unshift(b)
  form.buyer_id = b.id
  buyerForm.name = ''
  buyerDialog.value = false
}

async function submit() {
  if (!form.customer_id) return ElMessage.warning('客户必填')
  if (showBuyer.value && !form.buyer_id) return ElMessage.warning('公司客户需选择拿货人')
  const validItems = items.value.filter((r) => r.product_id && Number(r.qty) > 0).map((r) => ({ product_id: r.product_id, qty: Number(r.qty), unit_price: Number(r.unit_price || 0), note: null }))
  if (!validItems.length) return ElMessage.warning('请至少添加 1 行商品')

  saving.value = true
  try {
    const sale = await createSale({ sale_no: form.sale_no, customer_id: form.customer_id, buyer_id: showBuyer.value ? form.buyer_id : null, project: form.project || null, note: form.note || null, items: validItems })
    form.sale_no = sale.sale_no
    router.push(`/sales/${sale.id}`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await catalog.searchCustomers('')
  await catalog.searchProducts('')
  form.sale_no = (await getNextSaleNo()).sale_no
  const last = localStorage.getItem('shop:new_sale_last')
  if (last) {
    try {
      const parsed = JSON.parse(last)
      if (parsed.customer_id) {
        form.customer_id = parsed.customer_id
        await onCustomerChanged()
      }
      if (parsed.buyer_id) form.buyer_id = parsed.buyer_id
    } catch {}
  }
})
</script>
