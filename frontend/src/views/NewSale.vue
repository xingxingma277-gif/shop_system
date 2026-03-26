<template>
  <div v-show="step === 'form'">
    <el-card shadow="never" class="mb-12">
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight:700;">新建订单</div>
          <el-button type="primary" @click="goToNextStep">{{ form.order_stage === 'QUOTE' ? '下一步' : '去结算并开单' }}</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="90px">
        <el-form-item label="单据类型" required>
          <el-radio-group v-model="form.order_stage">
            <el-radio-button label="QUOTE">报价单 (暂不扣库存)</el-radio-button>
            <el-radio-button label="SALE_CONFIRMED">销售单</el-radio-button>
          </el-radio-group>
        </el-form-item>

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
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight:700;">商品明细</div>
          <el-button type="primary" @click="addRow">
            <el-icon style="margin-right: 4px"><Plus /></el-icon> 添加一行商品
          </el-button>
        </div>
      </template>
      <el-table :data="state.items" border :row-key="rowKey">
        <el-table-column label="商品" min-width="260">
          <template #default="{ row, $index }">
            <el-select v-model="row.product_id" filterable remote clearable :remote-method="onSearchProducts" style="width:100%" @change="()=>onProductChanged(row, $index)">
              <el-option v-for="p in catalog.products" :key="p.id" :label="`${p.name}${p.is_active ? '' : '（已停售）'}`" :value="p.id" :disabled="!p.is_active" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="当前库存" min-width="90">
          <template #default="{ row }">
            <span :style="{color: row.stock_qty < row.qty && form.order_stage === 'SALE_CONFIRMED' ? 'red' : 'inherit'}">
              {{ row.stock_qty != null ? row.stock_qty : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="数量" min-width="150">
          <template #default="{ row }"><el-input-number v-model="row.qty" :min="0.01" style="width: 130px;" /></template>
        </el-table-column>
        <el-table-column label="单价" min-width="380">
          <template #default="{ row }">
            <el-input-number v-model="row.unit_price" :min="0" style="width: 130px;" />
            <el-button v-if="row.lastPrice != null" size="small" type="success" plain style="margin-left:8px" @click="applyLastPrice(row)">用上次价格</el-button>
            <el-tooltip content="查看历史拿价" placement="top">
              <el-button circle plain size="large" :disabled="!canQueryPricing(row)" style="margin-left:8px" @click="openHistory(row)"><el-icon><Clock /></el-icon></el-button>
            </el-tooltip>
            <el-tag v-if="row.lastPrice != null" type="warning" style="margin-left:8px">上次拿价：¥{{ money(row.lastPrice) }}</el-tag>
            <el-tag v-if="showPriceDeviation(row)" type="danger" style="margin-left:8px">偏离上次价 {{ priceDeviationPercent(row) }}%</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="小计" min-width="120"><template #default="{ row }">{{ money((row.qty || 0) * (row.unit_price || 0)) }}</template></el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button type="danger" link @click="removeRow($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>

  <!-- 第二步：订单结算界面 -->
  <div v-if="step === 'checkout'">
    <el-card shadow="never">
      <template #header><div style="font-weight:700">销售单确认（付款确认）</div></template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="单号">{{ form.sale_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ customerName }}</el-descriptions-item>
        <el-descriptions-item label="拿货人" v-if="showBuyer">{{ buyerName }}</el-descriptions-item>
        <el-descriptions-item label="应收总额"><span style="color:#d4380d; font-weight:bold; font-size:16px;">¥{{ money(checkoutTotal) }}</span></el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <el-form label-width="110px">
        <el-form-item label="结算状态">
          <el-radio-group v-model="checkoutForm.settlement_status" @change="onStatusChange">
            <el-radio-button label="UNPAID">未付款 (挂账)</el-radio-button>
            <el-radio-button label="PARTIAL">部分付款 (首付)</el-radio-button>
            <el-radio-button label="PAID">已付清</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="本次首付金额" v-if="checkoutForm.settlement_status !== 'UNPAID'">
          <el-input-number v-model="checkoutForm.paid_amount" :min="0" :max="checkoutTotal" :disabled="checkoutForm.settlement_status === 'PAID'" style="width:260px" />
          <span style="margin-left:8px;color:#666">范围：0 ~ {{ money(checkoutTotal) }}</span>
        </el-form-item>

        <el-form-item label="付款方式" v-if="checkoutForm.settlement_status !== 'UNPAID'">
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <el-button v-for="m in paymentMethods" :key="m.value" :type="checkoutForm.payment_method === m.value ? 'primary' : 'default'" @click="checkoutForm.payment_method = m.value">{{ m.label }}{{ checkoutForm.payment_method === m.value ? ' ✓' : '' }}</el-button>
          </div>
        </el-form-item>

        <el-form-item label="备注/其他说明"><el-input v-model="checkoutForm.payment_note" placeholder="可选" /></el-form-item>
      </el-form>

      <div style="display:flex;justify-content:flex-end;gap:12px;">
        <el-button @click="step = 'form'">返回修改商品</el-button>
        <el-button type="primary" :loading="saving" @click="submitFinal">确认并保存交易</el-button>
      </div>
    </el-card>
  </div>

  <!-- 以下为原有组件和历史窗口，不赘述 -->
  <el-dialog v-model="historyDialog" title="历史拿价" width="85%" style="max-width: 1200px;">
    <el-table :data="historyRows" border size="small">
      <el-table-column prop="sale_no" label="单号" min-width="150" show-overflow-tooltip />
      <el-table-column prop="date" label="时间" min-width="140" show-overflow-tooltip>
        <template #default="{row}">{{ fmt(row.date) }}</template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" min-width="140" show-overflow-tooltip />
      <el-table-column prop="product_name" label="商品" min-width="180" show-overflow-tooltip />
      <el-table-column prop="unit_price" label="单价" min-width="90" />
      <el-table-column prop="qty" label="数量" min-width="80" />
      <el-table-column label="总金额" min-width="90"><template #default="{ row }">{{ money((row.qty || 0) * (row.unit_price || 0)) }}</template></el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" @click="useHistoryPrice(row)">使用该价</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
      <span style="color:#666; font-size:14px;">共 {{ historyMeta.total }} 条历史记录</span>
      <el-pagination background layout="prev, pager, next" v-model:current-page="historyPage" :page-size="historyPageSize" :total="historyMeta.total" @current-change="onHistoryPageChange" />
    </div>
  </el-dialog>

  <el-dialog v-model="buyerDialog" title="新增拿货人" width="420px">
    <el-form label-width="80px"><el-form-item label="姓名"><el-input v-model="buyerForm.name" /></el-form-item></el-form>
    <template #footer><el-button @click="buyerDialog=false">取消</el-button><el-button type="primary" @click="submitBuyer">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { Clock, Plus } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCatalogStore } from '../stores/catalog'
import { useDictsStore } from '../stores/dicts'
import { createBuyer, getCustomerProductPriceHistory, listBuyers } from '../api/customers'
import { getLastPricing } from '../api/pricing'
import { createSale, getNextSaleNo, getSaleApi } from '../api/sales'
import { formatDateTime, money } from '../utils/format'

const router = useRouter()
const catalog = useCatalogStore()
const dicts = useDictsStore()

const form = reactive({ order_stage: 'SALE_CONFIRMED', sale_no: '', customer_id: null, buyer_id: null, project: '', note: '' })
const buyers = ref([])
const saving = ref(false)
const buyerDialog = ref(false)
const buyerForm = reactive({ name: '' })
const rowSeed = ref(1)

const step = ref('form')

const paymentMethods = computed(() => dicts.paymentMethods)

const checkoutForm = reactive({
  settlement_status: 'PAID',
  paid_amount: 0,
  payment_method: null,
  payment_note: ''
})

const customerName = computed(() => catalog.customers.find((x) => x.id === form.customer_id)?.name || '-')
const buyerName = computed(() => buyers.value.find((x) => x.id === form.buyer_id)?.name || '-')
const checkoutTotal = computed(() => state.items.reduce((sum, row) => sum + ((row.qty || 0) * (row.unit_price || 0)), 0))

const newItemRow = () => ({ _key: rowSeed.value++, product_id: null, product_name: '', spec: '', stock_qty: null, quantity: 1, qty: 1, unit: '', unit_price: 0, amount: 0, subtotal: 0, remark: '', note: null, history: [], lastPrice: null })
const state = reactive({ items: [newItemRow()] })

const historyDialog = ref(false)
const historyRows = ref([])
const historyMeta = reactive({ total: 0 })
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyCurrentProductId = ref(null)
const selectedHistoryRow = ref(null)

const showBuyer = computed(() => (catalog.customers.find((x) => x.id === form.customer_id)?.type !== 'personal'))
const onSearchCustomers = (q) => catalog.searchCustomers(q || '')
const onSearchProducts = (q) => catalog.searchProducts(q || '')
const fmt = (v) => formatDateTime(v)
const rowKey = (row) => row._key

function onStatusChange(val) {
  if (val === 'UNPAID') { checkoutForm.paid_amount = 0; checkoutForm.payment_method = null }
  else if (val === 'PAID') checkoutForm.paid_amount = checkoutTotal.value
  else if (val === 'PARTIAL') if (checkoutForm.paid_amount === 0 || checkoutForm.paid_amount === checkoutTotal.value) checkoutForm.paid_amount = 0
}

async function goToNextStep() {
  if (!form.customer_id) return ElMessage.warning('请选择客户')
  if (showBuyer.value && !form.buyer_id) return ElMessage.warning('公司客户需选择拿货人')

  const validItems = state.items.filter((r) => r.product_id && Number(r.qty) > 0)
  if (!validItems.length) return ElMessage.warning('请至少添加 1 行商品明细并填写数量')

  const productIds = validItems.map(i => i.product_id)
  if (new Set(productIds).size !== productIds.length) {
    return ElMessage.warning("同一订单中不允许重复添加相同商品，请直接修改原商品行数量")
  }

  if (form.order_stage === 'SALE_CONFIRMED') {
    // 检查库存
    const outOfStock = validItems.find(r => r.stock_qty != null && Number(r.stock_qty) < Number(r.qty))
    if (outOfStock) {
      return ElMessage.warning(`商品【${outOfStock.product_name}】当前库存仅剩 ${outOfStock.stock_qty}，不足以完成此单！若需开单请改为“报价单”。`)
    }

    checkoutForm.settlement_status = 'PAID'
    checkoutForm.paid_amount = checkoutTotal.value
    checkoutForm.payment_method = null
    checkoutForm.payment_note = ''
    step.value = 'checkout'
  } else {
    // 如果是报价单，直接提交保存
    await submitDirectly()
  }
}

async function submitDirectly() {
  if (saving.value) return
  saving.value = true
  try {
    const validItems = state.items.filter((r) => r.product_id && Number(r.qty) > 0).map((r) => ({ product_id: r.product_id, qty: Number(r.qty), unit_price: Number(r.unit_price || 0), note: null }))
    const sale = await createSale({
      sale_no: form.sale_no,
      customer_id: form.customer_id,
      buyer_id: showBuyer.value ? form.buyer_id : null,
      project: form.project || null,
      note: form.note || null,
      order_stage: form.order_stage,
      order_type: form.order_stage === "QUOTE" ? "quote" : "sale_direct",
      items: validItems
    })
    ElMessage.success('报价单保存成功')
    await router.push(`/sales/${sale.id}`)
  } catch (err) {
    ElMessage.error(String(err?.response?.data?.detail || err?.message || '单据保存失败'))
  } finally { saving.value = false }
}

async function submitFinal() {
  if (saving.value) return
  if (checkoutForm.settlement_status !== 'UNPAID' && !checkoutForm.payment_method) {
    return ElMessage.warning('请选择付款方式')
  }

  saving.value = true
  try {
    const validItems = state.items.filter((r) => r.product_id && Number(r.qty) > 0).map((r) => ({ product_id: r.product_id, qty: Number(r.qty), unit_price: Number(r.unit_price || 0), note: null }))
    const sale = await createSale({
      sale_no: form.sale_no,
      customer_id: form.customer_id,
      buyer_id: showBuyer.value ? form.buyer_id : null,
      project: form.project || null,
      note: form.note || null,
      order_stage: form.order_stage,
      order_type: "sale_direct",
      settlement_status: checkoutForm.settlement_status,
      paid_amount: Number(checkoutForm.paid_amount || 0),
      payment_method: checkoutForm.settlement_status === "UNPAID" ? null : checkoutForm.payment_method,
      payment_note: checkoutForm.payment_note || null,
      items: validItems
    })
    ElMessage.success('销售单创建成功')
    await router.push(`/sales/${sale.id}`)
  } catch (err) {
    ElMessage.error(String(err?.response?.data?.detail || err?.message || '单据保存失败'))
  } finally { saving.value = false }
}

async function onCustomerChanged() {
  if (!form.customer_id) { buyers.value = []; form.buyer_id = null; return }
  try {
    buyers.value = await listBuyers(form.customer_id)
    const c = catalog.customers.find((x) => x.id === form.customer_id)
    if (c) form.buyer_id = c.type === 'personal' ? null : buyers.value[0]?.id || null
  } catch (err) {
    buyers.value = []; form.buyer_id = null
    if (err?.response?.status === 404) form.customer_id = null
  }
}

async function onProductChanged(row, index) {
  if (!row.product_id) return

  // 防重复检查
  const duplicates = state.items.filter((it, idx) => it.product_id === row.product_id && idx !== index)
  if (duplicates.length > 0) {
    ElMessage.error("该商品已在订单中存在，请勿重复添加")
    row.product_id = null
    return
  }

  const p = catalog.products.find((x) => x.id === row.product_id)
  row.product_name = p?.name || ''
  row.unit = p?.unit || ''
  row.unit_price = Number(p?.standard_price || 0)
  row.stock_qty = p?.stock_quantity != null ? Number(p.stock_quantity) : null

  if (canQueryPricing(row)) {
    try {
      const last = await getLastPricing({ customer_id: form.customer_id, product_id: row.product_id })
      row.lastPrice = last?.found ? Number(last.last_price) : null
    } catch (err) { row.lastPrice = null }
  }
}

function canQueryPricing(row) { return !!form.customer_id && !!row.product_id }
function priceDeviationPercent(row) { if (row.lastPrice == null || Number(row.lastPrice) === 0) return 0; return Math.round((Math.abs(Number(row.unit_price || 0) - Number(row.lastPrice)) / Number(row.lastPrice)) * 100) }
function showPriceDeviation(row) { return row.lastPrice != null && priceDeviationPercent(row) >= 20 }
function applyLastPrice(row) { if (row.lastPrice != null) { row.unit_price = Number(row.lastPrice); row.amount = Number(row.qty || 0) * Number(row.unit_price || 0) } }

function useHistoryPrice(row) {
  if (!row) return
  if (selectedHistoryRow.value && row.unit_price != null) {
    selectedHistoryRow.value.unit_price = Number(row.unit_price)
  }
  historyDialog.value = false
}

async function loadHistoryData() {
  if (!historyCurrentProductId.value || !form.customer_id) return
  try {
    const res = await getCustomerProductPriceHistory(form.customer_id, historyCurrentProductId.value, { page: historyPage.value, page_size: historyPageSize.value })
    historyRows.value = res.items || []
    historyMeta.total = res.meta?.total || 0
  } catch (err) {}
}

function onHistoryPageChange(p) { historyPage.value = p; loadHistoryData() }

async function openHistory(row) {
  if (!canQueryPricing(row)) return
  selectedHistoryRow.value = row
  historyCurrentProductId.value = row.product_id
  historyPage.value = 1
  await loadHistoryData()
  historyDialog.value = true
}

function addRow() { state.items.push(newItemRow()) }
function removeRow(index) { state.items.splice(index, 1) }
function openBuyerDialog() { buyerDialog.value = true }

async function submitBuyer() {
  if (!form.customer_id || !buyerForm.name.trim()) return
  try {
    const b = await createBuyer(form.customer_id, { name: buyerForm.name })
    buyers.value.unshift(b)
    form.buyer_id = b.id
    buyerForm.name = ''
    buyerDialog.value = false
  } catch (err) { ElMessage.error('创建拿货人失败') }
}

onMounted(async () => {
  try { await catalog.searchCustomers(''); await catalog.searchProducts('') } catch (e) {}
  try { form.sale_no = (await getNextSaleNo()).sale_no } catch (e) {}

  const last = localStorage.getItem('shop:new_sale_last')
  if (last) {
    try {
      const parsed = JSON.parse(last)
      if (parsed.customer_id && catalog.customers.find(c => c.id === parsed.customer_id)) {
        form.customer_id = parsed.customer_id
        await onCustomerChanged()
        if (parsed.buyer_id) form.buyer_id = parsed.buyer_id
      }
    } catch (e) { localStorage.removeItem('shop:new_sale_last') }
  }
})
</script>