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
        <el-select
          v-model="form.customer_id"
          filterable remote clearable
          placeholder="搜索客户"
          :remote-method="onSearchCustomers"
          :loading="customerLoading"
          style="width: 320px"
          @change="onCustomerChanged"
        >
          <el-option v-for="c in catalog.customers" :key="c.id" :label="c.name" :value="c.id">
            <div style="display:flex;justify-content:space-between;gap:12px;">
              <span>{{ c.name }}</span>
              <span class="muted">{{ c.phone || '' }}</span>
            </div>
          </el-option>
        </el-select>

        <el-button v-if="form.customer_id" type="info" plain @click="goProfile" style="margin-left:8px;">
          查看档案
        </el-button>

        <span v-else class="muted" style="margin-left:8px;">
          开单页仅可选择客户，编辑请到「客户管理/档案」
        </span>
      </el-form-item>

      <el-form-item label="时间">
        <el-date-picker v-model="form.sale_date" type="datetime" placeholder="默认当前时间" style="width: 320px" />
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.note" placeholder="可选" />
      </el-form-item>
    </el-form>
  </el-card>

  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <div style="font-weight:700;">商品明细</div>
        <div>
          <el-button @click="addRow">添加一行</el-button>
          <el-button type="danger" plain @click="clearAll" :disabled="items.length===0">清空</el-button>
        </div>
      </div>
    </template>

    <el-table :data="items" border size="small" row-key="_key">
      <el-table-column label="商品" min-width="260">
        <template #default="{ row }">
          <el-select
            v-model="row.product_id"
            filterable remote clearable
            placeholder="搜索商品"
            :remote-method="(q)=>onSearchProducts(q)"
            :loading="productLoading"
            style="width: 100%;"
            @change="()=>onProductChanged(row)"
          >
            <el-option v-for="p in catalog.products" :key="p.id" :label="p.name" :value="p.id">
              <div style="display:flex;justify-content:space-between;gap:10px;">
                <span>{{ p.name }}</span>
                <span class="muted">{{ p.sku || '' }}</span>
              </div>
            </el-option>
          </el-select>

          <div v-if="row.product" class="muted" style="margin-top:6px;">
            标准价：¥{{ money(row.product.standard_price) }} <span v-if="row.product.unit">/ {{ row.product.unit }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="数量" width="140">
        <template #default="{ row }">
          <el-input-number v-model="row.qty" :min="0.01" :step="1" controls-position="right" style="width: 120px" />
        </template>
      </el-table-column>

      <el-table-column label="成交价" min-width="260">
        <template #default="{ row }">
          <div style="display:flex;align-items:center;gap:8px;">
            <el-input-number
              v-model="row.sold_price"
              :min="0"
              :step="1"
              controls-position="right"
              style="width: 160px"
            />

            <el-popover
              placement="top"
              width="420"
              trigger="hover"
              @show="()=>ensureHistory(row)"
            >
              <template #reference>
                <el-button :disabled="!canQueryPricing(row)" circle plain>
                  <el-icon><Clock /></el-icon>
                </el-button>
              </template>

              <div style="font-weight:700;margin-bottom:8px;">
                该客户 - 该商品历史（最近20条）
              </div>

              <div v-if="row.historyLoading" class="muted">加载中...</div>
              <div v-else-if="!row.history || row.history.length===0" class="muted">暂无历史</div>

              <el-table v-else :data="row.history" size="small" border height="240">
                <el-table-column prop="date" label="日期" width="150">
                  <template #default="{ row: h }">{{ d(h.date) }}</template>
                </el-table-column>
                <el-table-column prop="qty" label="数量" width="90" />
                <el-table-column prop="sold_price" label="成交价" width="120">
                  <template #default="{ row: h }">¥{{ money(h.sold_price) }}</template>
                </el-table-column>
                <el-table-column prop="sale_id" label="单号" width="80" />
              </el-table>
            </el-popover>
          </div>

          <div v-if="row.lastInfo?.found" style="margin-top:6px;">
            <el-tag type="warning" effect="plain">
              上次：¥{{ money(row.lastInfo.last_price) }}（{{ d(row.lastInfo.last_date) }}，数量 {{ row.lastInfo.last_qty }}）
            </el-tag>
            <el-button link type="primary" @click="useLastPrice(row)" style="margin-left:8px;">
              一键填入上次价
            </el-button>
          </div>

          <div v-else-if="row.lastInfo && !row.lastInfo.found" class="muted" style="margin-top:6px;">
            该客户暂无此商品历史；可参考标准价。
          </div>
        </template>
      </el-table-column>

      <el-table-column label="小计" width="140">
        <template #default="{ row }">
          <span class="money">¥{{ money(lineTotal(row)) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="备注" min-width="160">
        <template #default="{ row }">
          <el-input v-model="row.remark" placeholder="可选" />
        </template>
      </el-table-column>

      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" link @click="removeRow(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;">
      <div>
        <span class="muted">总计：</span>
        <span class="money">¥{{ money(totalAmount) }}</span>
      </div>

      <el-button type="primary" :loading="saving" @click="submit">
        保存单据
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'

import { useCatalogStore } from '../stores/catalog'
import { createSale } from '../api/sales'
import { getLastPricing, getPricingHistory } from '../api/pricing'
import { debounceByKey } from '../utils/debounce'
import { money, d } from '../utils/format'

const router = useRouter()
const catalog = useCatalogStore()

const form = reactive({
  customer_id: null,
  sale_date: new Date(),
  note: ''
})

const saving = ref(false)
const customerLoading = ref(false)
const productLoading = ref(false)

function makeKey() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function newRow() {
  return {
    _key: makeKey(),
    product_id: null,
    product: null,
    qty: 1,
    sold_price: 0,
    remark: '',
    lastInfo: null,
    historyKey: null,
    history: [],
    historyLoading: false
  }
}

const items = reactive([newRow()])

const totalAmount = computed(() => {
  return items.reduce((sum, r) => sum + lineTotal(r), 0)
})

function lineTotal(row) {
  const qty = Number(row.qty || 0)
  const price = Number(row.sold_price || 0)
  const v = qty * price
  return Math.round(v * 100) / 100
}

function canQueryPricing(row) {
  return !!(form.customer_id && row.product_id)
}

const debouncedLast = debounceByKey(async (params) => {
  return await getLastPricing(params)
}, 300)

const debouncedHistory = debounceByKey(async (params) => {
  return await getPricingHistory(params)
}, 300)

async function onSearchCustomers(q) {
  customerLoading.value = true
  try {
    await catalog.searchCustomers(q || '')
  } finally {
    customerLoading.value = false
  }
}

async function onSearchProducts(q) {
  productLoading.value = true
  try {
    await catalog.searchProducts(q || '')
  } finally {
    productLoading.value = false
  }
}

function findProductById(id) {
  return catalog.products.find(p => p.id === id) || null
}

async function onCustomerChanged() {
  for (const row of items) {
    row.lastInfo = null
    row.history = []
    row.historyKey = null
    if (row.product_id) {
      await fetchLast(row)
    }
  }
}

async function onProductChanged(row) {
  row.product = row.product_id ? findProductById(row.product_id) : null

  if (row.product) {
    row.sold_price = Number(row.product.standard_price || 0)
  } else {
    row.sold_price = 0
  }

  row.lastInfo = null
  row.history = []
  row.historyKey = null

  await fetchLast(row)
}

async function fetchLast(row) {
  if (!canQueryPricing(row)) return
  try {
    const data = await debouncedLast(row._key, { customer_id: form.customer_id, product_id: row.product_id })
    row.lastInfo = data || null
  } catch (e) {}
}

async function ensureHistory(row) {
  if (!canQueryPricing(row)) return
  const key = `${form.customer_id}-${row.product_id}`
  if (row.historyKey === key && Array.isArray(row.history)) return

  row.historyKey = key
  row.historyLoading = true
  try {
    const list = await debouncedHistory(row._key, { customer_id: form.customer_id, product_id: row.product_id, limit: 20 })
    row.history = Array.isArray(list) ? list : []
  } catch (e) {
  } finally {
    row.historyLoading = false
  }
}

function useLastPrice(row) {
  if (row.lastInfo?.found) {
    row.sold_price = Number(row.lastInfo.last_price || 0)
  }
}

function addRow() {
  items.push(newRow())
}

function removeRow(row) {
  const idx = items.findIndex(r => r._key === row._key)
  if (idx >= 0) items.splice(idx, 1)
  if (items.length === 0) items.push(newRow())
}

async function clearAll() {
  await ElMessageBox.confirm('确认清空所有明细？', '提示', { type: 'warning' })
  items.splice(0, items.length, newRow())
}

function goProfile() {
  if (!form.customer_id) return
  router.push(`/customers/${form.customer_id}`)
}

async function submit() {
  if (!form.customer_id) {
    ElMessage.warning('请先选择客户')
    return
  }

  const validItems = items
    .filter(r => r.product_id && Number(r.qty) > 0)
    .map(r => ({
      product_id: r.product_id,
      qty: Number(r.qty),
      sold_price: Number(r.sold_price || 0),
      remark: r.remark || null
    }))

  if (validItems.length === 0) {
    ElMessage.warning('请至少添加 1 行商品明细')
    return
  }

  const payload = {
    customer_id: form.customer_id,
    sale_date: form.sale_date ? new Date(form.sale_date).toISOString() : null,
    note: form.note || null,
    items: validItems
  }

  saving.value = true
  try {
    const res = await createSale(payload)
    ElMessage.success(`保存成功：单号 #${res.id}，总计 ¥${money(res.total_amount)}`)
    router.push(`/customers/${form.customer_id}`)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await onSearchCustomers('')
  await onSearchProducts('')
})
</script>
