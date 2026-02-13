<template>
  <el-card v-if="sale">
    <template #header><div style="font-weight:700">订单结算</div></template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="单号">{{ sale.sale_no }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ sale.customer_name }}</el-descriptions-item>
      <el-descriptions-item label="应收总额">¥{{ money(sale.total_amount) }}</el-descriptions-item>
      <el-descriptions-item label="日期">{{ formatDateTime(sale.sale_date) }}</el-descriptions-item>
    </el-descriptions>

    <el-divider />

    <div style="margin-bottom:12px;display:flex;gap:8px;">
      <el-button :type="form.settlement_status==='UNPAID'?'primary':'default'" @click="setStatus('UNPAID')">未付款</el-button>
      <el-button :type="form.settlement_status==='PARTIAL'?'primary':'default'" @click="setStatus('PARTIAL')">部分付款</el-button>
      <el-button :type="form.settlement_status==='PAID'?'primary':'default'" @click="setStatus('PAID')">已付款</el-button>
    </div>

    <el-form label-width="110px">
      <el-form-item label="本次收款金额" v-if="form.settlement_status!=='UNPAID'">
        <el-input-number v-model="form.paid_amount" :min="0" :max="sale.total_amount" :disabled="form.settlement_status==='PAID'" style="width:260px" />
        <span style="margin-left:8px;color:#666">范围：0 ~ {{ money(sale.total_amount) }}</span>
      </el-form-item>

      <el-form-item label="付款方式" v-if="form.settlement_status!=='UNPAID'">
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <el-button v-for="m in methods" :key="m.value" :type="form.payment_method===m.value ? 'primary' : 'default'" @click="form.payment_method=m.value">{{ m.label }}{{ form.payment_method===m.value ? ' ✓' : '' }}</el-button>
        </div>
      </el-form-item>

      <el-form-item label="备注/其他说明"><el-input v-model="form.payment_note" placeholder="可选" /></el-form-item>
    </el-form>

    <div style="display:flex;justify-content:flex-end;gap:8px;">
      <el-button @click="goDetail">返回详情</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存结算</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSaleApi, submitSaleSettlement } from '../api/sales'
import { formatDateTime, money } from '../utils/format'

const route = useRoute()
const router = useRouter()
const saleId = Number(route.params.id)
const sale = ref(null)
const saving = ref(false)

const methods = [
  { label: '现金', value: 'cash' },
  { label: '微信', value: 'wechat' },
  { label: '支付宝', value: 'alipay' },
  { label: '银行转账', value: 'bank_transfer' },
]

const form = reactive({
  settlement_status: 'UNPAID',
  paid_amount: 0,
  payment_method: null,
  payment_note: '',
})

function setStatus(status) {
  form.settlement_status = status
  if (status === 'UNPAID') {
    form.paid_amount = 0
    form.payment_method = null
  }
  if (status === 'PAID' && sale.value) {
    form.paid_amount = Number(sale.value.total_amount)
  }
}

async function load() {
  sale.value = await getSaleApi(saleId)
  form.settlement_status = sale.value.settlement_status || 'UNPAID'
  form.paid_amount = Number(sale.value.paid_amount || 0)
  form.payment_method = sale.value.payment_method || null
  form.payment_note = sale.value.payment_note || ''
  if (form.settlement_status === 'PAID') form.paid_amount = Number(sale.value.total_amount)
}

async function submit() {
  saving.value = true
  try {
    await submitSaleSettlement(saleId, {
      settlement_status: form.settlement_status,
      paid_amount: Number(form.paid_amount || 0),
      payment_method: form.settlement_status === 'UNPAID' ? null : form.payment_method,
      payment_note: form.payment_note || null,
    })
    ElMessage.success('结算已保存')
    router.push(`/sales/${saleId}`)
  } finally {
    saving.value = false
  }
}

function goDetail() { router.push(`/sales/${saleId}`) }

onMounted(load)
</script>
