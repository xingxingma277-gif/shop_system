<template>
  <el-card v-if="sale">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div style="font-weight:700">订单详情 <el-tag :type="stageTag(sale.order_stage)" style="margin-left: 8px">{{ stageText(sale.order_stage) }}</el-tag></div>
        <div style="display:flex;gap:8px;">
          <!-- 打印预览 -->
          <el-dropdown @command="onPrint">
            <el-button type="success">打印单据<el-icon class="el-icon--right"><arrow-down /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="quote">打印报价单</el-dropdown-item>
                <el-dropdown-item command="sale" :disabled="sale.order_stage === 'QUOTE'">打印销售单</el-dropdown-item>
                <el-dropdown-item command="delivery" :disabled="sale.order_stage === 'QUOTE'">打印送货单</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button type="warning" plain v-if="sale.order_stage === 'QUOTE' && sale.biz_status !== 'VOIDED'" @click="handleConvertToSale">转为销售清单</el-button>
          <el-button type="warning" plain v-if="sale.order_stage === 'SALE_CONFIRMED' && sale.biz_status !== 'VOIDED'" @click="handleGenerateDelivery">生成送货单</el-button>

          <el-button type="primary" plain @click="onContinue">继续开单</el-button>
          <el-button type="primary" @click="onProfile">查看客户档案</el-button>
        </div>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="单号">{{ sale.sale_no }}</el-descriptions-item>
      <el-descriptions-item label="日期时间">{{ fmt(sale.sale_date) }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ sale.customer_name }}</el-descriptions-item>
      <el-descriptions-item label="电话">{{ customerPhone }}</el-descriptions-item>
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
      <span>最后结算方式：{{ paymentMethodText(sale.payment_method) }}</span>
      <el-tag :type="statusTag(sale.settlement_status || sale.payment_status)">{{ statusText(sale.settlement_status || sale.payment_status) }}</el-tag>
    </div>

    <el-divider v-if="payments.length > 0" />
    <div v-if="payments.length > 0">
      <div style="font-weight: bold; margin-bottom: 8px;">收款流水</div>
      <el-table :data="payments" border size="small">
        <el-table-column prop="paid_at" label="时间" width="160"><template #default="{row}">{{ fmt(row.paid_at) }}</template></el-table-column>
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="scene" label="款项类型" width="140">
           <template #default="{row}">
              <el-tag v-if="row.scene === 'ORDER_CHECKOUT'" type="info" size="small">开单首付/全款</el-tag>
              <el-tag v-else-if="row.scene === 'REVERSAL'" type="danger" size="small">撤销/冲销</el-tag>
              <el-tag v-else type="success" size="small">后续还款</el-tag>
           </template>
        </el-table-column>
        <el-table-column prop="method" label="方式" width="100"><template #default="{row}">{{ paymentMethodText(row.method) }}</template></el-table-column>
        <el-table-column prop="note" label="备注" />
      </el-table>
    </div>

    <!-- 打印预览弹窗 -->
    <el-dialog v-model="printDialog" title="打印单据预览 (原生格式)" width="850px" top="5vh">
      <div v-loading="pdfLoading" style="height: 65vh; min-height: 500px; width: 100%; border: 1px solid #dcdfe6; background: #f5f7fa;">
        <iframe v-if="pdfUrl" :src="pdfUrl" width="100%" height="100%" style="border: none;"></iframe>
        <div v-else-if="!pdfLoading" style="text-align: center; padding-top: 100px; color: #999;">
          未能加载 PDF 预览
        </div>
      </div>

      <template #footer>
        <el-button @click="printDialog = false">关闭</el-button>
        <el-button type="success" plain @click="downloadExcel">下载 Excel 存档</el-button>
        <el-button type="primary" :disabled="!pdfUrl" @click="doPrint">直接打印此单据</el-button>
      </template>
    </el-dialog>

  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { getSaleApi, getSalePaymentRecords, convertToSale, generateDelivery } from '../api/sales'
import { formatDateTime, money } from '../utils/format'
import http from '../api/http'
import { useDictsStore } from '../stores/dicts'

const route = useRoute()
const router = useRouter()
const dicts = useDictsStore()

const sale = ref(null)
const payments = ref([])
const printDialog = ref(false)
const customerPhone = ref('-')
const pdfUrl = ref(null)
const pdfLoading = ref(false)
const printDocType = ref('sale')

const fmt = (v) => formatDateTime(v, 'YYYY-MM-DD HH:mm')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清', UNPAID: '未结清', PARTIAL: '部分结清', PAID: '已结清' }[v] || '-')
const statusTag = (v) => ({ unpaid: 'danger', partial: 'warning', paid: 'success', UNPAID: 'danger', PARTIAL: 'warning', PAID: 'success' }[v] || 'info')
const stageText = (v) => ({ QUOTE: '报价单', SALE_CONFIRMED: '销售单', DELIVERY_CREATED: '已生成送货单' }[v] || v)
const stageTag = (v) => ({ QUOTE: 'info', SALE_CONFIRMED: 'primary', DELIVERY_CREATED: 'success' }[v] || 'info')

function paymentMethodText(v) {
  const f = dicts.paymentMethods.find(m => m.value === v)
  return f ? f.label : (v || '-')
}

async function loadData() {
  const id = Number(route.params.id)
  sale.value = await getSaleApi(id)
  if (sale.value && sale.value.customer_id) {
    try {
      const res = await http.get(`/api/customers/${sale.value.customer_id}`)
      customerPhone.value = res.data.phone || res.data.mobile || res.data.contact_phone || '-'
    } catch (e) { customerPhone.value = '-' }
  }

  try {
    const pRes = await getSalePaymentRecords(id)
    payments.value = pRes.items || []
  } catch (e) {}
}

async function handleConvertToSale() {
  await ElMessageBox.confirm('将正式扣除商品库存。如库存不足将无法转换。是否继续？', '转换确认', { type: 'warning' })
  try {
    await convertToSale(sale.value.id)
    ElMessage.success('已成功转为销售清单并扣除库存')
    await loadData()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '转换失败')
  }
}

async function handleGenerateDelivery() {
  try {
    await generateDelivery(sale.value.id)
    ElMessage.success('已生成送货单阶段记录')
    await loadData()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '生成失败')
  }
}

async function onPrint(command) {
  printDocType.value = command
  printDialog.value = true
  pdfUrl.value = null
  pdfLoading.value = true
  try {
    const res = await http.get(`/api/sales/${sale.value.id}/export_pdf`, {
      params: { doc_type: command },
      responseType: 'blob'
    })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    pdfUrl.value = window.URL.createObjectURL(blob)
  } catch (err) {
    ElMessage.error('加载打印预览失败，请检查 Excel 是否卡死或环境配置。')
  } finally {
    pdfLoading.value = false
  }
}

async function downloadExcel() {
  try {
    const res = await http.get(`/api/sales/${sale.value.id}/export_excel`, {
      params: { doc_type: printDocType.value },
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    const nameMap = { quote: "报价单", sale: "销售清单", delivery: "送货单" }
    link.setAttribute('download', `${nameMap[printDocType.value]}_${sale.value.sale_no}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    ElMessage.error('下载失败，请确保 backend 目录下有打印模板.xlsx。')
  }
}

function doPrint() {
  if (!pdfUrl.value) return
  const iframe = document.createElement('iframe')
  iframe.style.display = 'none'
  iframe.src = pdfUrl.value
  document.body.appendChild(iframe)
  iframe.onload = () => {
    setTimeout(() => {
      iframe.contentWindow.focus()
      iframe.contentWindow.print()
      setTimeout(() => document.body.removeChild(iframe), 5000)
    }, 200)
  }
}

function onContinue() {
  if (sale.value) {
    localStorage.setItem('shop:new_sale_last', JSON.stringify({ customer_id: sale.value.customer_id, buyer_id: sale.value.buyer_id }))
  }
  router.push('/new-sale')
}

function onProfile() { if (sale.value?.customer_id) router.push(`/customers/${sale.value.customer_id}`) }

onMounted(loadData)
</script>