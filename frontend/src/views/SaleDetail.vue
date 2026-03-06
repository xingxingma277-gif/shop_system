<template>
  <el-card v-if="sale">
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div style="font-weight:700">订单详情</div>
        <div style="display:flex;gap:8px;">
          <el-button @click="onPrint">打印预览</el-button>
          <el-button type="primary" plain @click="onContinue">继续开单</el-button>
          <el-button type="primary" @click="onProfile">查看客户档案</el-button>
        </div>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="单号">{{ sale.sale_no }}</el-descriptions-item>
      <el-descriptions-item label="日期时间">{{ fmt(sale.sale_date) }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ sale.customer_name }}</el-descriptions-item>
      <el-descriptions-item label="拿货人" v-if="sale.buyer_name">{{ sale.buyer_name }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ sale.note || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />
    <el-table :data="sale.items || []" border>
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="sku" label="SKU" min-width="120" />
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

    <!-- 修复：优雅的打印预览与下载窗口 -->
    <el-dialog v-model="printDialog" title="打印/下载预览" width="800px">
      <div id="print-area" style="padding: 20px; font-family: sans-serif; color: #000;">
        <h2 style="text-align: center; margin-bottom: 20px;">销售清单</h2>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px;">
          <span>单号：{{ sale.sale_no }}</span>
          <span>日期：{{ fmt(sale.sale_date) }}</span>
        </div>
        <div style="margin-bottom: 10px; font-size: 14px;">客户名称：{{ sale.customer_name }}</div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;" border="1">
          <thead>
            <tr style="background-color: #f2f2f2;">
              <th style="padding: 8px;">序号</th>
              <th style="padding: 8px;">商品</th>
              <th style="padding: 8px;">SKU</th>
              <th style="padding: 8px;">单位</th>
              <th style="padding: 8px;">数量</th>
              <th style="padding: 8px;">单价</th>
              <th style="padding: 8px;">金额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(it, idx) in sale.items" :key="idx" style="text-align: center;">
              <td style="padding: 8px;">{{ idx + 1 }}</td>
              <td style="padding: 8px;">{{ it.product_name }}</td>
              <td style="padding: 8px;">{{ it.sku || '-' }}</td>
              <td style="padding: 8px;">{{ it.unit || '-' }}</td>
              <td style="padding: 8px;">{{ it.qty }}</td>
              <td style="padding: 8px;">{{ it.unit_price }}</td>
              <td style="padding: 8px;">{{ it.line_total }}</td>
            </tr>
          </tbody>
        </table>

        <div style="text-align: right; margin-top: 10px; font-weight: bold; font-size: 16px;">
          合计：¥{{ money(sale.total_amount) }}
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 40px; font-size: 14px;">
          <span>发货人（签字）：_______________</span>
          <span>收货人（签字）：_______________</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="printDialog = false">关闭</el-button>
        <el-button type="success" plain @click="downloadExcel">直接下载 Excel</el-button>
        <el-button type="primary" @click="doPrint">网页端打印</el-button>
      </template>
    </el-dialog>

  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSaleApi } from '../api/sales'
import { formatDateTime, money } from '../utils/format'
import http from '../api/http'

const route = useRoute()
const router = useRouter()
const sale = ref(null)
const printDialog = ref(false)

const fmt = (v) => formatDateTime(v)
const statusText = (v) => ({ unpaid: '未结清', partial: '部分结清', paid: '已结清', UNPAID: '未结清', PARTIAL: '部分结清', PAID: '已结清' }[v] || '-')
const statusTag = (v) => ({ unpaid: 'danger', partial: 'warning', paid: 'success', UNPAID: 'danger', PARTIAL: 'warning', PAID: 'success' }[v] || 'info')
const paymentMethodText = (v) => ({ cash: '现金', wechat: '微信', alipay: '支付宝', bank_transfer: '银行转账' }[v] || '-')

function onPrint() {
  printDialog.value = true
}

// 直接使用浏览器默认机制下载，避免 Blob 数据强行转后缀名导致打不开
function downloadExcel() {
  const baseUrl = http.defaults.baseURL || 'http://127.0.0.1:8000'
  window.open(`${baseUrl}/api/sales/${sale.value.id}/export_excel`, '_blank')
}

// 提取内容在浏览器新标签页中打开进行物理打印
function doPrint() {
  const content = document.getElementById('print-area').innerHTML
  const win = window.open('', '_blank')
  win.document.write('<html><head><title>打印销售清单</title></head><body>')
  win.document.write(content)
  win.document.write('</body></html>')
  win.document.close()
  win.focus()
  setTimeout(() => {
    win.print()
    win.close()
  }, 200)
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
})
</script>