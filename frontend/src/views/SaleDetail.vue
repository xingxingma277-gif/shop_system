<template>
  <el-card v-if="sale">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div style="font-weight:700">订单详情</div>
        <div style="display:flex;gap:8px;">
          <!-- 打印预览按钮 -->
          <el-button type="success" @click="onPrint">打印预览</el-button>
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
      <span>付款方式：{{ paymentMethodText(sale.payment_method) }}</span>
      <el-tag :type="statusTag(sale.settlement_status || sale.payment_status)">{{ statusText(sale.settlement_status || sale.payment_status) }}</el-tag>
    </div>

    <!-- 打印预览弹窗：完全抛弃网页排版，直接内嵌原生 PDF 文件，100%还原Excel -->
    <el-dialog v-model="printDialog" title="打印单据预览 (原生格式)" width="850px" top="5vh">
      <div v-loading="pdfLoading" style="height: 65vh; min-height: 500px; width: 100%; border: 1px solid #dcdfe6; background: #f5f7fa;">
        <!-- 如果加载成功，直接展示 PDF -->
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
import { ElMessage } from 'element-plus'
import { getSaleApi } from '../api/sales'
import { formatDateTime, money } from '../utils/format'
import http from '../api/http'

const route = useRoute()
const router = useRouter()
const sale = ref(null)
const printDialog = ref(false)
const customerPhone = ref('-')
const pdfUrl = ref(null)
const pdfLoading = ref(false)

const fmt = (v) => formatDateTime(v, 'YYYY-MM-DD HH:mm')
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清', UNPAID: '未结清', PARTIAL: '部分结清', PAID: '已结清' }[v] || '-')
const statusTag = (v) => ({ unpaid: 'danger', partial: 'warning', paid: 'success', UNPAID: 'danger', PARTIAL: 'warning', PAID: 'success' }[v] || 'info')
const paymentMethodText = (v) => ({ cash: '现金', wechat: '微信', alipay: '支付宝', bank_transfer: '银行转账' }[v] || '-')

// 点击预览时，请求后端的 PDF 文件并展示
async function onPrint() {
  printDialog.value = true
  if (!pdfUrl.value) {
    pdfLoading.value = true
    try {
      const res = await http.get(`/api/sales/${sale.value.id}/export_pdf`, {
        responseType: 'blob'
      })
      // 将返回的二进制流转为 PDF 可见链接
      const blob = new Blob([res.data], { type: 'application/pdf' })
      pdfUrl.value = window.URL.createObjectURL(blob)
    } catch (err) {
      ElMessage.error('加载打印预览失败，请检查 Excel 是否卡死或环境配置。')
    } finally {
      pdfLoading.value = false
    }
  }
}

// 正常下载 Excel 表格
async function downloadExcel() {
  try {
    const res = await http.get(`/api/sales/${sale.value.id}/export_excel`, {
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `销售清单_${sale.value.sale_no}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

  } catch (err) {
    ElMessage.error('下载失败，请确保 backend 目录下有打印模板.xlsx。')
  }
}

// 直接打印生成的 PDF 文件，这样打出来的单据和您的 Excel 模板百分百一致
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
      // 打印完毕后可选择性移除 iframe，保持页面整洁
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

onMounted(async () => {
  sale.value = await getSaleApi(Number(route.params.id))

  if (sale.value && sale.value.customer_id) {
    try {
      const res = await http.get(`/api/customers/${sale.value.customer_id}`)
      customerPhone.value = res.data.phone || res.data.mobile || res.data.contact_phone || '-'
    } catch (e) {
      console.warn('获取客户真实电话失败', e)
      customerPhone.value = '-'
    }
  }
})
</script>