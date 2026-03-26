<template>
  <el-card v-if="sale">
    <template #header>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
          <div style="font-weight:700;display:flex;align-items:center;gap:8px;">
            订单详情
            <el-tag :type="stageTag(sale.order_stage)">{{ stageText(sale.order_stage) }}</el-tag>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <el-button v-if="backLabel" @click="backToOrigin">{{ backLabel }}</el-button>
            <el-button @click="continueCreate">继续开单</el-button>
            <el-button type="primary" plain @click="createForCurrentCustomer">再为当前客户开一单</el-button>
            <el-button v-if="mainAction" type="primary" @click="mainAction.handler">{{ mainAction.label }}</el-button>
            <el-dropdown @command="onSecondaryCommand">
              <el-button>更多操作<el-icon class="el-icon--right"><arrow-down /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="print_quote">导出报价单</el-dropdown-item>
                  <el-dropdown-item command="print_sale" :disabled="sale.order_stage === 'QUOTE'">导出销售单</el-dropdown-item>
                  <el-dropdown-item command="print_delivery" :disabled="sale.order_stage === 'QUOTE'">导出送货单</el-dropdown-item>
                  <el-dropdown-item command="profile">查看客户档案</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <el-alert
          v-if="showSubmitSuccess"
          title="开单成功，您可以继续处理下一张单据。"
          type="success"
          :closable="false"
          show-icon
        >
          <template #default>
            <div style="display:flex;gap:8px;margin-top:8px;">
              <el-button size="small" @click="continueCreate">继续开单</el-button>
              <el-button size="small" type="primary" plain @click="createForCurrentCustomer">再为当前客户开一单</el-button>
            </div>
          </template>
        </el-alert>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="单号">{{ sale.sale_no }}</el-descriptions-item>
      <el-descriptions-item label="日期时间">{{ fmt(sale.sale_date) }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ sale.customer_name }}</el-descriptions-item>
      <el-descriptions-item label="送货状态">{{ deliveryText(sale.delivery_status) }}</el-descriptions-item>
      <el-descriptions-item label="收货信息" :span="2">{{ deliveryReceiverText }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ sale.note || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />
    <el-table :data="sale.items || []" border>
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="sku" label="规格" min-width="120" />
      <el-table-column prop="qty" label="数量" width="110" />
      <el-table-column prop="unit_price" label="单价" width="110" />
      <el-table-column prop="line_total" label="小计" width="120" />
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:12px;gap:16px;">
      <span>应收：¥{{ money(sale.total_amount) }}</span>
      <span>已收：¥{{ money(sale.paid_amount) }}</span>
      <span style="color:#d4380d">未收：¥{{ money(sale.ar_amount) }}</span>
      <el-tag :type="statusTag(sale.settlement_status || sale.payment_status)">{{ statusText(sale.settlement_status || sale.payment_status) }}</el-tag>
    </div>

    <el-divider v-if="payments.length > 0" />
    <el-table v-if="payments.length > 0" :data="payments" border size="small">
      <el-table-column prop="paid_at" label="时间" width="160"><template #default="{row}">{{ fmt(row.paid_at) }}</template></el-table-column>
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="scene" label="记录语义" width="150">
        <template #default="{row}">
          <el-tag v-if="row.scene === 'ORDER_CHECKOUT'" type="info" size="small">订单付款</el-tag>
          <el-tag v-else-if="row.scene === 'REVERSAL'" type="danger" size="small">冲销</el-tag>
          <el-tag v-else type="success" size="small">后续收款</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="method" label="方式" width="100"><template #default="{row}">{{ paymentMethodText(row.method) }}</template></el-table-column>
      <el-table-column prop="note" label="备注" />
    </el-table>
  </el-card>

  <el-dialog v-model="convertDialog" title="确认转为销售单" width="560px">
    <el-form label-width="120px">
      <el-form-item label="付款状态">
        <el-select v-model="convertForm.settlement_status" style="width:220px">
          <el-option label="未付款" value="UNPAID" />
          <el-option label="部分付款" value="PARTIAL" />
          <el-option label="已付款" value="PAID" />
        </el-select>
      </el-form-item>
      <el-form-item label="付款方式" v-if="convertForm.settlement_status !== 'UNPAID'">
        <el-select v-model="convertForm.payment_method" style="width:220px">
          <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="已付金额" v-if="convertForm.settlement_status === 'PARTIAL'">
        <el-input-number v-model="convertForm.paid_amount" :min="0" :max="sale?.total_amount || 0" />
      </el-form-item>
      <el-form-item label="需要送货">
        <el-switch v-model="convertForm.needs_delivery" />
      </el-form-item>
      <template v-if="convertForm.needs_delivery">
        <el-form-item label="收货人"><el-input v-model="convertForm.receiver_name" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="convertForm.receiver_phone" /></el-form-item>
        <el-form-item label="收货地址"><el-input v-model="convertForm.receiver_address" /></el-form-item>
      </template>
      <el-form-item label="备注"><el-input v-model="convertForm.payment_note" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="convertDialog=false">返回报价单</el-button>
      <el-button type="primary" @click="submitConvert">确认转为销售单</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="deliveryDialog" title="生成送货单" width="520px">
    <el-form label-width="110px">
      <el-form-item label="收货人"><el-input v-model="deliveryForm.receiver_name" /></el-form-item>
      <el-form-item label="联系电话"><el-input v-model="deliveryForm.receiver_phone" /></el-form-item>
      <el-form-item label="收货地址"><el-input v-model="deliveryForm.receiver_address" /></el-form-item>
      <el-form-item label="送货备注"><el-input v-model="deliveryForm.delivery_note" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="deliveryDialog=false">取消</el-button>
      <el-button type="primary" @click="submitDelivery">确认生成</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { convertToSale, exportSaleExcel, generateDelivery, getSaleApi, getSalePaymentRecords } from '../api/sales'
import { formatDateTime, money } from '../utils/format'
import { useDictsStore } from '../stores/dicts'
import { useSaleWizardStore } from '../stores/saleWizard'

const route = useRoute()
const router = useRouter()
const dicts = useDictsStore()
const wizardStore = useSaleWizardStore()
const paymentMethods = computed(() => dicts.paymentMethods)

const sale = ref(null)
const payments = ref([])
const convertDialog = ref(false)
const deliveryDialog = ref(false)
const convertForm = reactive({ settlement_status: 'UNPAID', payment_method: null, paid_amount: 0, payment_note: '', needs_delivery: false, receiver_name: '', receiver_phone: '', receiver_address: '' })
const deliveryForm = reactive({ receiver_name: '', receiver_phone: '', receiver_address: '', delivery_note: '' })

const showSubmitSuccess = computed(() => route.query.from_submit === '1')
const fmt = (v) => formatDateTime(v, 'YYYY-MM-DD HH:mm')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清', UNPAID: '未结清', PARTIAL: '部分结清', PAID: '已结清' }[v] || '-')
const statusTag = (v) => ({ unpaid: 'danger', partial: 'warning', paid: 'success', UNPAID: 'danger', PARTIAL: 'warning', PAID: 'success' }[v] || 'info')
const stageText = (v) => ({ QUOTE: '报价中', SALE_CONFIRMED: '销售已确认', DELIVERY_PENDING: '待送货', DELIVERY_CREATED: '已生成送货单', DELIVERED: '已送达' }[v] || v)
const stageTag = (v) => ({ QUOTE: 'info', SALE_CONFIRMED: 'primary', DELIVERY_PENDING: 'warning', DELIVERY_CREATED: 'success', DELIVERED: 'success' }[v] || 'info')
const deliveryText = (v) => ({ NONE: '无需送货', PENDING: '待生成送货单', GENERATED: '已生成送货单', SHIPPED: '已发货', SIGNED: '已签收' }[v] || v)

const backLabel = computed(() => route.query.return_to === 'transactions' ? '返回交易记录' : '')

const deliveryReceiverText = computed(() => {
  if (!sale.value?.needs_delivery) return '无需送货'
  const s = sale.value
  return `${s.receiver_name || '-'} / ${s.receiver_phone || '-'} / ${s.receiver_address || '-'}`
})

const mainAction = computed(() => {
  if (!sale.value) return null
  if (sale.value.order_stage === 'QUOTE') return { label: '转为销售单', handler: () => openConvertDialog() }
  if (sale.value.order_stage === 'SALE_CONFIRMED' && sale.value.ar_amount > 0) return { label: sale.value.paid_amount > 0 ? '继续收款' : '去收款', handler: () => router.push(`/sales/${sale.value.id}/payment`) }
  if (sale.value.order_stage === 'SALE_CONFIRMED' && sale.value.needs_delivery && sale.value.delivery_status !== 'GENERATED') return { label: '生成送货单', handler: () => openDeliveryDialog() }
  if (sale.value.order_stage === 'DELIVERY_CREATED') return { label: '查看/导出送货单', handler: () => downloadDoc('delivery') }
  return null
})

function continueCreate() {
  wizardStore.clearDraft()
  router.push('/sales/wizard/step1')
}

function createForCurrentCustomer() {
  wizardStore.clearDraft()
  wizardStore.customerInfo = {
    id: sale.value.customer_id,
    name: sale.value.customer_name,
    type: sale.value.customer_type || 'company'
  }
  wizardStore.buyerId = sale.value.buyer_id || null
  wizardStore.buyerName = sale.value.buyer_name || ''
  wizardStore.items = []
  wizardStore.totalAmount = 0
  wizardStore.settlement = {
    settlement_status: 'PAID',
    paid_amount: 0,
    payment_method: 'bank_transfer',
    payment_note: ''
  }
  wizardStore.setCurrentStep(2)
  wizardStore.saveDraftToLocal()
  router.push('/sales/wizard/step2')
}

function backToOrigin() {
  if (route.query.return_to === 'transactions') {
    const query = {}
    if (typeof route.query.tab === 'string') query.tab = route.query.tab
    if (typeof route.query.status === 'string') query.status = route.query.status
    if (typeof route.query.preset === 'string') query.preset = route.query.preset
    if (typeof route.query.start_date === 'string') query.start_date = route.query.start_date
    if (typeof route.query.end_date === 'string') query.end_date = route.query.end_date
    if (typeof route.query.source === 'string') query.source = route.query.source
    if (typeof route.query.context === 'string') query.context = route.query.context
    router.push({ path: '/transactions', query })
  }
}

function paymentMethodText(v) {
  const f = dicts.paymentMethods.find((m) => m.value === v)
  return f ? f.label : (v || '-')
}

async function loadData() {
  const id = Number(route.params.id)
  sale.value = await getSaleApi(id)
  const pRes = await getSalePaymentRecords(id)
  payments.value = pRes.items || []
}

function openConvertDialog() {
  convertForm.settlement_status = 'UNPAID'
  convertForm.payment_method = null
  convertForm.paid_amount = 0
  convertForm.needs_delivery = false
  convertForm.receiver_name = sale.value?.receiver_name || ''
  convertForm.receiver_phone = sale.value?.receiver_phone || ''
  convertForm.receiver_address = sale.value?.receiver_address || ''
  convertDialog.value = true
}

async function submitConvert() {
  try {
    await convertToSale(sale.value.id, { ...convertForm })
    ElMessage.success('报价已转为销售单')
    convertDialog.value = false
    await loadData()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '转换失败')
  }
}

function openDeliveryDialog() {
  deliveryForm.receiver_name = sale.value?.receiver_name || ''
  deliveryForm.receiver_phone = sale.value?.receiver_phone || ''
  deliveryForm.receiver_address = sale.value?.receiver_address || ''
  deliveryForm.delivery_note = sale.value?.delivery_note || ''
  deliveryDialog.value = true
}

async function submitDelivery() {
  try {
    await generateDelivery(sale.value.id, { ...deliveryForm })
    ElMessage.success('已生成送货单')
    deliveryDialog.value = false
    await loadData()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '生成失败')
  }
}

async function downloadDoc(docType) {
  try {
    const blob = await exportSaleExcel(sale.value.id, docType)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    const nameMap = { quote: '报价单', sale: '销售清单', delivery: '送货单' }
    a.href = url
    a.download = `${nameMap[docType]}_${sale.value.sale_no}.xlsx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    ElMessage.error('导出失败')
  }
}

function onSecondaryCommand(cmd) {
  if (cmd === 'profile') router.push(`/customers/${sale.value.customer_id}`)
  if (cmd === 'print_quote') downloadDoc('quote')
  if (cmd === 'print_sale') downloadDoc('sale')
  if (cmd === 'print_delivery') downloadDoc('delivery')
}

onMounted(loadData)
</script>
