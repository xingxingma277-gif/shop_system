<template>
  <div>
    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="12">
        <el-card>
          <template #header>客户信息</template>
          <div><b>{{ customer?.name }}</b>（{{ customer?.type === 'company' ? '公司' : '个人' }}）</div>
          <div>联系人：{{ customer?.contact_name || '-' }}</div>
          <div>电话：{{ customer?.phone || '-' }}</div>
          <div>地址：{{ customer?.address || '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>欠款概览</template>
          <div>累计销售：¥{{ ar.total_sales.toFixed(2) }}</div>
          <div>累计已收：¥{{ ar.total_received.toFixed(2) }}</div>
          <div>累计欠款：<b style="color:#d4380d">¥{{ ar.total_ar.toFixed(2) }}</b></div>
          <el-button type="primary" style="margin-top:8px" @click="receiptDialog=true">收款/还款</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:10px; flex-wrap:wrap">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="~" start-placeholder="开始" end-placeholder="结束" />
        <el-input v-model="filters.q" placeholder="搜索单号/项目/拿货人" style="width:240px" clearable />
        <el-select v-model="filters.payment_status" clearable placeholder="结算状态" style="width:140px">
          <el-option label="未结清" value="unpaid" /><el-option label="部分结清" value="partial" /><el-option label="已结清" value="paid" />
        </el-select>
        <el-select v-model="filters.sort_by" style="width:140px">
          <el-option label="最新在前" value="date_desc" />
          <el-option label="最早在前" value="date_asc" />
          <el-option label="欠款优先" value="ar_desc" />
        </el-select>
        <el-button @click="quickDays(7)">近7天</el-button>
        <el-button @click="quickDays(30)">近30天</el-button>
        <el-button @click="thisMonth">本月</el-button>
        <el-button type="primary" @click="loadStatement">查询</el-button>
        <el-button @click="exportCsv">导出CSV</el-button>
      </div>

      <el-tabs v-model="tab" @tab-change="onTab">
        <el-tab-pane label="公司总账单" name="statement">
          <el-table :data="statement.items" border :height="tableHeight" empty-text="当前筛选无数据">
            <el-table-column prop="sale_no" label="单号" min-width="160" />
            <el-table-column prop="date" label="日期" min-width="160">
              <template #default="{ row }">{{ fmt(row.date) }}</template>
            </el-table-column>
            <el-table-column prop="project" label="项目" min-width="140" />
            <el-table-column prop="buyer_name" label="拿货人" min-width="120" />
            <el-table-column prop="total" label="总额" width="100" />
            <el-table-column prop="paid" label="已付" width="100" />
            <el-table-column prop="ar" label="未付" width="100" />
            <el-table-column prop="status" label="状态" width="110">
              <template #default="{ row }">
                <el-tag v-if="row.status==='paid'" type="success">已结清</el-tag>
                <el-tag v-else-if="row.status==='partial'" type="warning">部分结清</el-tag>
                <el-tag v-else type="danger">未结清</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="按拿货人账单" name="buyer">
          <el-select v-model="buyerId" placeholder="选择拿货人" style="width:260px;margin-bottom:10px" @change="loadBuyerStatement">
            <el-option v-for="b in buyers" :key="b.id" :value="b.id" :label="b.name" />
          </el-select>
          <el-table :data="buyerStatement.items" border :height="tableHeight" empty-text="当前筛选无数据">
            <el-table-column prop="sale_id" label="单号" width="100" />
            <el-table-column prop="date" label="日期" min-width="160"><template #default="{ row }">{{ fmt(row.date) }}</template></el-table-column>
            <el-table-column prop="project" label="项目" min-width="150" />
            <el-table-column prop="total" label="总额" width="100" />
            <el-table-column prop="paid" label="已付" width="100" />
            <el-table-column prop="ar" label="未付" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="receiptDialog" title="客户收款/还款" width="420px">
      <el-form label-width="90px">
        <el-form-item label="收款方式">
          <el-select v-model="receipt.method" style="width:100%">
            <el-option label="现金" value="cash" /><el-option label="微信" value="wechat" /><el-option label="支付宝" value="alipay" />
            <el-option label="银行卡" value="bank" /><el-option label="转账" value="transfer" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款金额"><el-input-number v-model="receipt.amount" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="receipt.note" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="receiptDialog=false">取消</el-button>
        <el-button type="primary" :loading="receipting" @click="submitReceipt">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api/http'
import { getCustomer, listBuyers } from '../api/customers'
import { createCustomerReceipt, exportCustomerStatementUrl, getCustomerArSummary, getCustomerStatement } from '../api/customers_ext'

const route = useRoute()
const customerId = Number(route.params.id)

const tableHeight = Math.max(window.innerHeight - 420, 260)
const tab = ref('statement')
const customer = ref(null)
const buyers = ref([])
const buyerId = ref(null)
const dateRange = ref([dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()])
const filters = reactive({ q: '', payment_status: '', sort_by: 'date_desc' })

const ar = reactive({ total_sales: 0, total_received: 0, total_ar: 0 })
const statement = reactive({ items: [] })
const buyerStatement = reactive({ items: [] })

const receiptDialog = ref(false)
const receipting = ref(false)
const receipt = reactive({ method: 'transfer', amount: 0, note: '', allocate_mode: 'oldest_first' })

function fmt(v) {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
}

function thisMonth() {
  dateRange.value = [dayjs().startOf('month').toDate(), dayjs().endOf('month').toDate()]
}

function quickDays(days) {
  dateRange.value = [dayjs().subtract(days, 'day').toDate(), dayjs().endOf('day').toDate()]
}

function buildParams() {
  return {
    page: 1,
    page_size: 50,
    start_date: dateRange.value?.[0] ? dayjs(dateRange.value[0]).format('YYYY-MM-DD') : undefined,
    end_date: dateRange.value?.[1] ? dayjs(dateRange.value[1]).format('YYYY-MM-DD') : undefined,
    q: filters.q || undefined,
    payment_status: filters.payment_status || undefined,
    sort_by: filters.sort_by,
  }
}

async function loadBase() {
  const rs = await Promise.allSettled([getCustomer(customerId), getCustomerArSummary(customerId), listBuyers(customerId)])
  if (rs[0].status === 'fulfilled') customer.value = rs[0].value
  if (rs[1].status === 'fulfilled') Object.assign(ar, rs[1].value)
  if (rs[2].status === 'fulfilled') {
    buyers.value = rs[2].value || []
    buyerId.value = buyers.value[0]?.id || null
  }
}

async function loadStatement() {
  const data = await getCustomerStatement(customerId, buildParams())
  statement.items = data.items || []
}

async function loadBuyerStatement() {
  if (!buyerId.value) return
  const params = buildParams()
  const data = await http.get(`/api/buyers/${buyerId.value}/statement`, { params }).then((r) => r.data)
  buyerStatement.items = data.items || []
}

function onTab() {
  if (tab.value === 'buyer') loadBuyerStatement().catch(() => ElMessage.error('拿货人账单加载失败'))
}

async function submitReceipt() {
  if (!receipt.amount || receipt.amount <= 0) return ElMessage.warning('请输入收款金额')
  receipting.value = true
  try {
    await createCustomerReceipt(customerId, receipt)
    ElMessage.success('收款完成并已自动分配')
    receiptDialog.value = false
    await loadBase()
    await loadStatement()
  } finally {
    receipting.value = false
  }
}

function exportCsv() {
  window.open(exportCustomerStatementUrl(customerId, buildParams()), '_blank')
}

onMounted(async () => {
  try {
    await loadBase()
    await loadStatement()
  } catch {
    ElMessage.error('客户档案加载失败')
  }
})
</script>
