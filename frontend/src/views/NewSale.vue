<template>
  <!-- 第一步：开单界面 -->
  <div v-show="step === 'form'">
    <el-card shadow="never" class="mb-12">
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight:700;">新建拿货单</div>
          <el-button type="primary" @click="goToCheckout">去结算</el-button>
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
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight:700;">商品明细</div>
          <!-- 🌟 优化：使“添加一行”按钮非常醒目，增加图标 -->
          <el-button type="primary" @click="addRow">
            <el-icon style="margin-right: 4px"><Plus /></el-icon> 添加一行商品
          </el-button>
        </div>
      </template>
      <el-table :data="state.items" border :row-key="rowKey">
        <el-table-column label="商品" min-width="260">
          <template #default="{ row }">
            <el-select v-model="row.product_id" filterable remote clearable :remote-method="onSearchProducts" style="width:100%" @change="()=>onProductChanged(row)">
              <el-option v-for="p in catalog.products" :key="p.id" :label="`${p.name}${p.is_active ? '' : '（已停售）'}`" :value="p.id" :disabled="!p.is_active" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="数量" min-width="160">
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
      <template #header><div style="font-weight:700">订单结算确认</div></template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="单号">{{ form.sale_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ customerName }}</el-descriptions-item>
        <el-descriptions-item label="拿货人" v-if="showBuyer">{{ buyerName }}</el-descriptions-item>
        <el-descriptions-item label="应收总额"><span style="color:#d4380d; font-weight:bold; font-size:16px;">¥{{ money(checkoutTotal) }}</span></el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <el-form label-width="110px">
        <!-- 🌟 优化：将状态改为单选按钮组，避免“点了没反应”的视觉错觉 -->
        <el-form-item label="结算状态">
          <el-radio-group v-model="checkoutForm.settlement_status" @change="onStatusChange">
            <el-radio-button label="UNPAID">未付款 (挂账)</el-radio-button>
            <el-radio-button label="PARTIAL">部分付款</el-radio-button>
            <el-radio-button label="PAID">已付清</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="本次收款金额" v-if="checkoutForm.settlement_status !== 'UNPAID'">
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

  <!-- 历史价格弹窗 -->
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
          <el-button link type="primary" @click="openHistoryDetail(row)">快捷预览</el-button>
          <el-button link type="success" @click="useHistoryPrice(row)">使用该价</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
      <span style="color:#666; font-size:14px;">共 {{ historyMeta.total }} 条历史记录</span>
      <el-pagination background layout="prev, pager, next" v-model:current-page="historyPage" :page-size="historyPageSize" :total="historyMeta.total" @current-change="onHistoryPageChange" />
    </div>
  </el-dialog>

  <!-- 详情侧边栏 -->
  <el-drawer v-model="historyDetailVisible" title="历史销售单明细" size="60%">
    <template v-if="historyDetail">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="单号" span="2">{{ historyDetail.sale_no }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ historyDetail.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ fmt(historyDetail.sale_date) }}</el-descriptions-item>
        <el-descriptions-item label="备注" span="2">{{ historyDetail.note || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <el-table :data="historyDetail.items || []" border>
        <el-table-column prop="product_name" label="商品" min-width="180" show-overflow-tooltip />
        <el-table-column prop="qty" label="数量" min-width="80" />
        <el-table-column prop="unit" label="单位" min-width="80" />
        <el-table-column prop="unit_price" label="单价" min-width="90" />
        <el-table-column prop="line_total" label="小计" min-width="100" />
      </el-table>
      <div style="margin-top:12px;display:flex;justify-content:flex-end;gap:10px;">
        <el-button @click="historyDetailVisible=false">关闭</el-button>
        <el-button type="success" @click="useHistoryPrice(selectedHistoryPriceRow)">仅使用该条历史价格</el-button>
      </div>
    </template>
  </el-drawer>

  <el-dialog v-model="buyerDialog" title="新增拿货人" width="420px">
    <el-form label-width="80px"><el-form-item label="姓名"><el-input v-model="buyerForm.name" /></el-form-item></el-form>
    <template #footer><el-button @click="buyerDialog=false">取消</el-button><el-button type="primary" @click="submitBuyer">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { Clock, Plus } from '@element-plus/icons-vue' // 引入了 Plus 图标
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCatalogStore } from '../stores/catalog'
import { createBuyer, getCustomerProductPriceHistory, listBuyers } from '../api/customers'
import { getLastPricing } from '../api/pricing'
import { createSale, getNextSaleNo, getSaleApi, submitSaleSettlement } from '../api/sales'
import { formatDateTime, money } from '../utils/format'

const router = useRouter()
const catalog = useCatalogStore()
const form = reactive({ sale_no: '', customer_id: null, buyer_id: null, project: '', note: '' })
const buyers = ref([])
const saving = ref(false)
const buyerDialog = ref(false)
const buyerForm = reactive({ name: '' })
const rowSeed = ref(1)

const step = ref('form')

const paymentMethods = [
  { label: '现金', value: 'cash' },
  { label: '微信', value: 'wechat' },
  { label: '支付宝', value: 'alipay' },
  { label: '银行转账', value: 'bank_transfer' },
]

const checkoutForm = reactive({
  settlement_status: 'PAID',
  paid_amount: 0,
  payment_method: null,
  payment_note: ''
})

const customerName = computed(() => {
  const c = catalog.customers.find((x) => x.id === form.customer_id)
  return c ? c.name : '-'
})

const buyerName = computed(() => {
  const b = buyers.value.find((x) => x.id === form.buyer_id)
  return b ? b.name : '-'
})

const checkoutTotal = computed(() => {
  return state.items.reduce((sum, row) => sum + ((row.qty || 0) * (row.unit_price || 0)), 0)
})

const newItemRow = () => ({ _key: rowSeed.value++, product_id: null, product_name: '', spec: '', quantity: 1, qty: 1, unit: '', unit_price: 0, amount: 0, subtotal: 0, remark: '', note: null, history: [], lastPrice: null })

const state = reactive({
  items: [newItemRow()]
})

const historyDialog = ref(false)
const historyRows = ref([])
const historyMeta = reactive({ total: 0 })
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyCurrentProductId = ref(null)

const historyDetailVisible = ref(false)
const historyDetail = ref(null)
const selectedHistoryRow = ref(null)
const selectedHistoryPriceRow = ref(null)

const showBuyer = computed(() => (catalog.customers.find((x) => x.id === form.customer_id)?.type !== 'personal'))
const onSearchCustomers = (q) => catalog.searchCustomers(q || '')
const onSearchProducts = (q) => catalog.searchProducts(q || '')
const fmt = (v) => formatDateTime(v)
const rowKey = (row) => row._key

// 🌟 优化：结账状态切换逻辑
function onStatusChange(val) {
  if (val === 'UNPAID') {
    checkoutForm.paid_amount = 0
    checkoutForm.payment_method = null
  } else if (val === 'PAID') {
    checkoutForm.paid_amount = checkoutTotal.value
  } else if (val === 'PARTIAL') {
    // 切换到部分付款时，强制归零，让用户手动输入真实的部分付款额
    if (checkoutForm.paid_amount === 0 || checkoutForm.paid_amount === checkoutTotal.value) {
      checkoutForm.paid_amount = 0
    }
  }
}

function goToCheckout() {
  if (!form.customer_id) return ElMessage.warning('请选择客户')
  if (showBuyer.value && !form.buyer_id) return ElMessage.warning('公司客户需选择拿货人')

  const validItems = state.items.filter((r) => r.product_id && Number(r.qty) > 0)
  if (!validItems.length) return ElMessage.warning('请至少添加 1 行商品明细并填写数量')

  checkoutForm.settlement_status = 'PAID'
  checkoutForm.paid_amount = checkoutTotal.value
  checkoutForm.payment_method = null
  checkoutForm.payment_note = ''

  step.value = 'checkout'
}

async function submitFinal() {
  if (saving.value) return
  if (checkoutForm.settlement_status !== 'UNPAID' && !checkoutForm.payment_method) {
    return ElMessage.warning('请选择付款方式')
  }

  const validItems = state.items.filter((r) => r.product_id && Number(r.qty) > 0).map((r) => ({ product_id: r.product_id, qty: Number(r.qty), unit_price: Number(r.unit_price || 0), note: null }))

  saving.value = true
  try {
    const sale = await createSale({
      sale_no: form.sale_no,
      customer_id: form.customer_id,
      buyer_id: showBuyer.value ? form.buyer_id : null,
      project: form.project || null,
      note: form.note || null,
      items: validItems
    })

    if (checkoutForm.settlement_status !== 'UNPAID') {
      await submitSaleSettlement(sale.id, {
        settlement_status: checkoutForm.settlement_status,
        paid_amount: Number(checkoutForm.paid_amount || 0),
        payment_method: checkoutForm.payment_method,
        payment_note: checkoutForm.payment_note || null,
      })
    }

    ElMessage.success('开单并结算成功')
    await router.push(`/sales/${sale.id}`)
  } catch (err) {
    let msg = err?.response?.data?.detail || err?.message || '单据保存失败'
    if (Array.isArray(msg)) msg = msg[0]?.msg || '参数校验失败'
    ElMessage.error(String(msg))
  } finally {
    saving.value = false
  }
}

// 🌟 修复重启卡死：增加安全 Try Catch 拦截
async function onCustomerChanged() {
  if (!form.customer_id) {
    buyers.value = []
    form.buyer_id = null
    return
  }
  try {
    buyers.value = await listBuyers(form.customer_id)
    const c = catalog.customers.find((x) => x.id === form.customer_id)
    if (c) {
      form.buyer_id = c.type === 'personal' ? null : buyers.value[0]?.id || null
    }
  } catch (err) {
    console.warn('获取拿货人失败，可能是数据库重置了', err)
    buyers.value = []
    form.buyer_id = null
    // 若报 404 说明这客户彻底不存在了，自动清空
    if (err?.response?.status === 404) {
      form.customer_id = null
    }
  }
}

async function onProductChanged(row) {
  if (!row.product_id) return
  const p = catalog.products.find((x) => x.id === row.product_id)
  row.product_name = p?.name || ''
  row.unit = p?.unit || ''
  row.unit_price = Number(p?.standard_price || 0)
  if (canQueryPricing(row)) {
    try {
      const last = await getLastPricing({ customer_id: form.customer_id, product_id: row.product_id })
      row.lastPrice = last?.found ? Number(last.last_price) : null
    } catch (err) {
      console.warn('获取历史报价失败', err)
      row.lastPrice = null
    }
  }
}

function canQueryPricing(row) {
  return !!form.customer_id && !!row.product_id
}

function priceDeviationPercent(row) {
  if (row.lastPrice == null || Number(row.lastPrice) === 0) return 0
  return Math.round((Math.abs(Number(row.unit_price || 0) - Number(row.lastPrice)) / Number(row.lastPrice)) * 100)
}

function showPriceDeviation(row) {
  if (row.lastPrice == null) return false
  return priceDeviationPercent(row) >= 20
}

function applyLastPrice(row) {
  if (row.lastPrice != null) {
    row.unit_price = Number(row.lastPrice)
    row.amount = Number(row.qty || 0) * Number(row.unit_price || 0)
    row.subtotal = row.amount
  }
}

function useHistoryPrice(row) {
  if (!row) return
  const current = selectedHistoryRow.value
  if (current && row.unit_price != null) {
    current.unit_price = Number(row.unit_price)
    current.amount = Number(current.qty || 0) * Number(current.unit_price || 0)
    current.subtotal = current.amount
  }
  historyDetailVisible.value = false
  historyDialog.value = false
}

async function loadHistoryData() {
  if (!historyCurrentProductId.value || !form.customer_id) return
  try {
    const res = await getCustomerProductPriceHistory(form.customer_id, historyCurrentProductId.value, {
      page: historyPage.value,
      page_size: historyPageSize.value
    })
    historyRows.value = (res.items || []).map((it) => ({
      ...it,
      customer_name: form.customer_id ? (catalog.customers.find((x) => x.id === form.customer_id)?.name || '') : '',
      product_name: catalog.products.find((p) => p.id === historyCurrentProductId.value)?.name || ''
    }))
    historyMeta.total = res.meta?.total || 0
    if (selectedHistoryRow.value) {
      selectedHistoryRow.value.history = historyRows.value
    }
  } catch (err) {
    console.warn('获取历史数据失败', err)
  }
}

function onHistoryPageChange(p) {
  historyPage.value = p
  loadHistoryData()
}

async function openHistory(row) {
  if (!canQueryPricing(row)) return
  selectedHistoryRow.value = row
  historyCurrentProductId.value = row.product_id
  historyPage.value = 1
  await loadHistoryData()
  historyDialog.value = true
}

async function openHistoryDetail(row) {
  if (!row?.sale_id) return
  selectedHistoryPriceRow.value = row
  try {
    const data = await getSaleApi(row.sale_id)
    historyDetail.value = data
    historyDetailVisible.value = true
  } catch (err) {
    ElMessage.error('无法加载订单详情')
  }
}

function addRow() {
  state.items.push(newItemRow())
}

function removeRow(index) {
  state.items.splice(index, 1)
}

function openBuyerDialog() { buyerDialog.value = true }

async function submitBuyer() {
  if (!form.customer_id || !buyerForm.name.trim()) return
  try {
    const b = await createBuyer(form.customer_id, { name: buyerForm.name })
    buyers.value.unshift(b)
    form.buyer_id = b.id
    buyerForm.name = ''
    buyerDialog.value = false
  } catch (err) {
    ElMessage.error('创建拿货人失败')
  }
}

// 🌟 修复重启卡死：全面防御机制，无惧重启清空数据库
onMounted(async () => {
  try {
    await catalog.searchCustomers('')
    await catalog.searchProducts('')
  } catch (e) {
    console.warn('获取目录失败', e)
  }

  try {
    form.sale_no = (await getNextSaleNo()).sale_no
  } catch (e) {
    console.warn('获取单号失败', e)
  }

  const last = localStorage.getItem('shop:new_sale_last')
  if (last) {
    try {
      const parsed = JSON.parse(last)
      if (parsed.customer_id) {
        // 先检查该客户在现在的数据库里还存不存在！
        const exists = catalog.customers.find(c => c.id === parsed.customer_id)
        if (exists) {
          form.customer_id = parsed.customer_id
          await onCustomerChanged()
          if (parsed.buyer_id) form.buyer_id = parsed.buyer_id
        } else {
          // 不存在说明后台重启清空了，直接删除旧缓存！
          localStorage.removeItem('shop:new_sale_last')
        }
      }
    } catch (e) {
      console.warn('处理旧缓存失败', e)
      localStorage.removeItem('shop:new_sale_last')
    }
  }
})
</script>