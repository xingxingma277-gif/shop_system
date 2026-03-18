<template>
  <el-card>
    <template #header><b>统一收款</b></template>
    <div v-if="sale">
      <p>单号 #{{ sale.sale_no }} ｜应收：¥{{ sale.total_amount.toFixed(2) }} ｜未收：¥{{ sale.ar_amount.toFixed(2) }}</p>
      <el-form label-width="100px">
        <el-form-item label="付款类型">
          <el-select v-model="form.pay_type" style="width:260px">
            <el-option label="付清 (全额补收)" value="paid_full" />
            <el-option label="部分付款" value="partial" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款方式">
          <el-select v-model="form.method" style="width:260px">
            <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款金额" v-if="form.pay_type==='partial'">
          <el-input-number v-model="form.amount" :min="0" :max="sale.ar_amount" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" /></el-form-item>
      </el-form>
      <el-button type="primary" :loading="saving" @click="submit">确认收款</el-button>
      <el-button @click="goProfile">返回订单详情</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSaleApi, submitSalePayment } from '../api/sales'
import { useDictsStore } from '../stores/dicts'

const route = useRoute()
const router = useRouter()
const dicts = useDictsStore()
const paymentMethods = computed(() => dicts.paymentMethods)

const saleId = Number(route.params.id || route.query.sale_id)
const sale = ref(null)
const saving = ref(false)
const form = reactive({ pay_type: "paid_full", method: "bank_transfer", amount: 0, note: "" })

async function loadSale() {
  sale.value = await getSaleApi(saleId)
  form.amount = sale.value?.ar_amount || 0
}

async function submit() {
  saving.value = true
  try {
    const payload = { ...form, scene: "POST_SALE_REPAYMENT" }
    if (payload.pay_type !== 'partial') delete payload.amount
    const res = await submitSalePayment(saleId, payload)
    sale.value = res.sale
    ElMessage.success('收款记录已保存')
  } finally {
    saving.value = false
  }
}

function goProfile() {
  if (sale.value?.id) router.push(`/sales/${sale.value.id}`)
}

onMounted(loadSale)
</script>