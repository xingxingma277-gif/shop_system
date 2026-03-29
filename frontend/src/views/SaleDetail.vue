<template>
  <el-card v-if="sale">
    <template #header>
      <div class="header-row">
        <div>
          <div class="title">{{ sale.sale_no }} <el-tag :type="stageTag(sale.order_stage)">{{ stageText(sale.order_stage) }}</el-tag></div>
          <div class="sub">客户：{{ sale.customer_name }}<span v-if="sale.source_quote_no"> ｜ 来源报价：{{ sale.source_quote_no }}</span></div>
        </div>
        <div class="actions">
          <el-button v-if="mainAction" type="primary" @click="mainAction.handler">{{ mainAction.label }}</el-button>
          <el-dropdown @command="onSecondaryCommand">
            <el-button>更多操作<el-icon class="el-icon--right"><arrow-down /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="preview_quote">预览报价单</el-dropdown-item>
                <el-dropdown-item command="preview_sale">预览销售单</el-dropdown-item>
                <el-dropdown-item command="preview_delivery">预览送货单</el-dropdown-item>
                <el-dropdown-item command="excel_quote">导出报价 Excel</el-dropdown-item>
                <el-dropdown-item command="excel_sale">导出销售 Excel</el-dropdown-item>
                <el-dropdown-item command="excel_delivery">导出送货 Excel</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>

    <el-alert v-if="showSubmitSuccess" title="开单成功" type="success" :closable="false" show-icon />

    <div class="center-grid">
      <el-card shadow="never" class="preview">
        <template #header>单据预览</template>
        <iframe v-if="previewUrl" :src="previewUrl" style="width:100%;height:460px;border:none" />
        <div v-else class="empty">请选择预览类型</div>
        <div class="preview-actions">
          <el-button @click="openPreview(currentDocType)">刷新预览</el-button>
          <el-button type="primary" @click="printPreview">打印</el-button>
          <el-button @click="downloadPdf(currentDocType)">下载 PDF</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>状态摘要与时间线</template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="结算状态">{{ statusText(sale.settlement_status || sale.payment_status) }}</el-descriptions-item>
          <el-descriptions-item label="应收/已收/未收">¥{{ money(sale.total_amount) }} / ¥{{ money(sale.paid_amount) }} / ¥{{ money(sale.ar_amount) }}</el-descriptions-item>
          <el-descriptions-item label="送货信息">{{ deliverySummary }}</el-descriptions-item>
        </el-descriptions>
        <el-timeline style="margin-top: 12px;">
          <el-timeline-item :timestamp="fmt(sale.created_at)">报价创建</el-timeline-item>
          <el-timeline-item :timestamp="fmt(sale.sale_confirmed_at)">销售确认</el-timeline-item>
          <el-timeline-item :timestamp="fmt(sale.delivery_created_at)">送货单生成</el-timeline-item>
          <el-timeline-item :timestamp="fmt(sale.delivered_at)">签收完成</el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <el-divider />
    <el-table :data="sale.items || []" border>
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="sku" label="规格" min-width="120" />
      <el-table-column prop="qty" label="数量" width="110" />
      <el-table-column prop="unit_price" label="单价" width="110" />
      <el-table-column prop="line_total" label="小计" width="120" />
    </el-table>

    <el-divider v-if="payments.length > 0" />
    <el-table v-if="payments.length > 0" :data="payments" border size="small">
      <el-table-column prop="paid_at" label="时间" width="160"><template #default="{ row }">{{ fmt(row.paid_at) }}</template></el-table-column>
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="method" label="方式" width="100"><template #default="{ row }">{{ paymentMethodText(row.method) }}</template></el-table-column>
      <el-table-column prop="note" label="备注" />
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { convertToSale, downloadSalePdf, exportSaleExcel, getSaleApi, getSalePaymentRecords, previewSalePdfUrl } from '../api/sales'
import { formatDateTime, money } from '../utils/format'
import { useDictsStore } from '../stores/dicts'
import { useSaleWizardStore } from '../stores/saleWizard'

const route = useRoute()
const router = useRouter()
const dicts = useDictsStore()
const wizardStore = useSaleWizardStore()

const sale = ref(null)
const payments = ref([])
const previewUrl = ref('')
const currentDocType = ref('sale')

const showSubmitSuccess = computed(() => route.query.from_submit === '1')
const fmt = (v) => formatDateTime(v, 'YYYY-MM-DD HH:mm')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清', UNPAID: '未结清', PARTIAL: '部分结清', PAID: '已结清' }[v] || '-')
const stageText = (v) => ({ QUOTE: '报价单', SALE_CONFIRMED: '销售单', DELIVERY_PENDING: '待送货', DELIVERY_CREATED: '已生成送货单', DELIVERED: '已送达' }[v] || v)
const stageTag = (v) => ({ QUOTE: 'info', SALE_CONFIRMED: 'primary', DELIVERY_PENDING: 'warning', DELIVERY_CREATED: 'success', DELIVERED: 'success' }[v] || 'info')

const deliverySummary = computed(() => {
  if (!sale.value) return '-'
  if (sale.value.needs_delivery || sale.value.delivery_status !== 'NONE') {
    return `${sale.value.receiver_name || '-'} / ${sale.value.receiver_phone || '-'} / ${sale.value.receiver_address || '-'}`
  }
  if (!sale.value.needs_delivery && sale.value.delivery_status === 'NONE' && !sale.value.receiver_name && !sale.value.receiver_phone && !sale.value.receiver_address) return '送货未设置'
  if (sale.value.needs_delivery === false) return '无需送货'
  return '送货未设置'
})

const mainAction = computed(() => {
  if (!sale.value) return null
  if (sale.value.order_stage === 'QUOTE' && sale.value.quote_status !== 'CONVERTED') {
    return { label: '转为销售单', handler: convertQuoteToSale }
  }
  if (sale.value.order_stage === 'QUOTE' && !['CONVERTED', 'VOIDED', 'EXPIRED'].includes(sale.value.quote_status || 'SUBMITTED')) {
    return { label: '编辑报价单', handler: editQuote }
  }
  return null
})

function editQuote() {
  wizardStore.clearDraft()
  wizardStore.orderType = 'quote'
  wizardStore.editingQuoteId = sale.value.id
  wizardStore.quoteUpdatedAt = sale.value.updated_at
  wizardStore.customerInfo = { id: sale.value.customer_id, name: sale.value.customer_name, type: 'company' }
  wizardStore.buyerId = sale.value.buyer_id || null
  wizardStore.buyerName = sale.value.buyer_name || ''
  wizardStore.project = sale.value.project || ''
  wizardStore.remark = sale.value.note || ''
  wizardStore.items = (sale.value.items || []).map((i) => ({ product_id: i.product_id, product_name: i.product_name, spec: i.sku, unit: i.unit, qty: i.qty, actual_price: i.unit_price, remark: i.note || '' }))
  wizardStore.totalAmount = sale.value.total_amount || 0
  wizardStore.setCurrentStep(3)
  wizardStore.saveDraftToLocal()
  router.push('/sales/wizard/step3')
}

async function convertQuoteToSale() {
  try {
    const converted = await convertToSale(sale.value.id, { settlement_status: 'UNPAID' })
    ElMessage.success('已转为销售单')
    router.replace(`/sales/${converted.id}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '转换失败')
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
  openPreview(sale.value.order_stage === 'QUOTE' ? 'quote' : sale.value.order_stage === 'DELIVERY_CREATED' ? 'delivery' : 'sale')
}

function openPreview(docType = 'sale') {
  currentDocType.value = docType
  previewUrl.value = previewSalePdfUrl(sale.value.id, docType)
}

function printPreview() {
  const w = window.open(previewUrl.value, '_blank')
  setTimeout(() => w?.print(), 600)
}

async function downloadPdf(docType) {
  const blob = await downloadSalePdf(sale.value.id, docType)
  const url = URL.createObjectURL(new Blob([blob]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${sale.value.sale_no}_${docType}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

async function downloadDoc(docType) {
  const blob = await exportSaleExcel(sale.value.id, docType)
  const url = URL.createObjectURL(new Blob([blob]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${sale.value.sale_no}_${docType}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}

function onSecondaryCommand(cmd) {
  if (cmd === 'preview_quote') openPreview('quote')
  if (cmd === 'preview_sale') openPreview('sale')
  if (cmd === 'preview_delivery') openPreview('delivery')
  if (cmd === 'excel_quote') downloadDoc('quote')
  if (cmd === 'excel_sale') downloadDoc('sale')
  if (cmd === 'excel_delivery') downloadDoc('delivery')
}

onMounted(loadData)
</script>

<style scoped>
.header-row { display:flex;justify-content:space-between;align-items:center;gap:12px; }
.title { font-weight:700;display:flex;align-items:center;gap:8px; }
.sub { color:#666;font-size:13px;margin-top:6px; }
.actions { display:flex;gap:8px; }
.center-grid { display:grid;grid-template-columns: 2fr 1fr;gap:12px;margin-top:12px; }
.empty { color:#999;height:460px;display:flex;align-items:center;justify-content:center; }
.preview-actions { display:flex;justify-content:flex-end;gap:8px;margin-top:8px; }
</style>
