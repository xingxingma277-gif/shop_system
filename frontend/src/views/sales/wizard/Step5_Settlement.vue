<template>
  <div class="step-container">
    <h3 class="step-title">第五步：结算并提交</h3>

    <el-card shadow="never" class="summary-card">
      <template #header>
        <div class="card-header">销售单信息</div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="单据类型">销售单</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ wizardStore.customerInfo?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拿货人">{{ wizardStore.buyerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="订单总额">¥ {{ Number(wizardStore.totalAmount || 0).toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-form label-width="120px" class="step-form">
      <el-form-item label="结算状态">
        <el-radio-group v-model="formData.settlement_status" @change="handleStatusChange">
          <el-radio-button label="UNPAID">未付款</el-radio-button>
          <el-radio-button label="PARTIAL">部分付款</el-radio-button>
          <el-radio-button label="PAID">已付清</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="实收金额" v-if="formData.settlement_status !== 'UNPAID'">
        <el-input-number
          v-model="formData.paid_amount"
          :min="0"
          :max="wizardStore.totalAmount"
          :precision="2"
          :disabled="formData.settlement_status === 'PAID'"
          style="width: 220px;"
        />
      </el-form-item>

      <el-form-item label="付款方式" v-if="formData.settlement_status !== 'UNPAID'">
        <el-select v-model="formData.payment_method" style="width: 220px;">
          <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
        </el-select>
      </el-form-item>

      <el-form-item label="付款备注">
        <el-input v-model="formData.payment_note" placeholder="可选" />
      </el-form-item>
    </el-form>

    <div class="step-actions">
      <el-button size="large" @click="goPrev" :disabled="submitting">返回确认订单</el-button>
      <el-button type="success" size="large" @click="submitOrder" :loading="submitting">确认并提交</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDictsStore } from '../../../stores/dicts'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useSaleWizardDraft } from '../../../composables/useSaleWizardDraft'
import { createSale } from '../../../api/sales'

const router = useRouter()
const dicts = useDictsStore()
const wizardStore = useSaleWizardStore()
const { save } = useSaleWizardDraft(wizardStore)

const paymentMethods = computed(() => dicts.paymentMethods)
const submitting = ref(false)

const formData = reactive({
  settlement_status: wizardStore.settlement?.settlement_status || 'PAID',
  paid_amount: wizardStore.settlement?.paid_amount ?? wizardStore.totalAmount,
  payment_method: wizardStore.settlement?.payment_method || 'bank_transfer',
  payment_note: wizardStore.settlement?.payment_note || ''
})

watch(
  () => ({ ...formData }),
  (val) => {
    wizardStore.settlement = { ...val }
    wizardStore.setCurrentStep(5)
    save()
  },
  { deep: true }
)

const handleStatusChange = (val) => {
  if (val === 'UNPAID') {
    formData.paid_amount = 0
  } else if (val === 'PAID') {
    formData.paid_amount = wizardStore.totalAmount
  } else if (formData.paid_amount === 0 || formData.paid_amount === wizardStore.totalAmount) {
    formData.paid_amount = 0
  }
}

const goPrev = () => {
  wizardStore.setCurrentStep(4)
  save()
  router.push('/sales/wizard/step4')
}

onMounted(() => {
  if (!wizardStore.customerInfo || wizardStore.items.length === 0) {
    ElMessage.warning('请先完成前序开单步骤')
    router.push('/sales/wizard/step1')
    return
  }
  if (wizardStore.orderType !== 'retail') {
    router.push('/sales/wizard/step4')
  }
})


const submitOrder = async () => {
  if (formData.settlement_status !== 'UNPAID' && !formData.payment_method) {
    return ElMessage.warning('请选择付款方式')
  }

  try {
    await ElMessageBox.confirm('确认提交销售单？', '提交确认', { type: 'warning' })
    submitting.value = true

    const payload = {
      customer_id: wizardStore.customerInfo.id,
      buyer_id: wizardStore.buyerId,
      order_stage: 'SALE_CONFIRMED',
      order_type: 'sale_direct',
      project: wizardStore.project || null,
      note: wizardStore.remark || null,
      source_quote_id: wizardStore.sourceQuoteId || null,
      settlement_status: formData.settlement_status,
      paid_amount: formData.paid_amount,
      payment_method: formData.settlement_status !== 'UNPAID' ? formData.payment_method : null,
      payment_note: formData.payment_note || null,
      items: wizardStore.items.map((item) => ({
        product_id: item.product_id,
        qty: item.qty,
        unit_price: item.actual_price,
        note: item.remark || null
      }))
    }

    const sale = await createSale(payload)
    wizardStore.markSubmitted()
    wizardStore.clearDraft()
    ElMessage.success('销售单提交成功')
    router.push(`/sales/${sale.id}?from_submit=1`)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error?.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.step-container { max-width: 820px; margin: 0 auto; padding-top: 20px; }
.step-title { text-align: center; margin-bottom: 20px; color: #303133; font-weight: 600; }
.summary-card { margin-bottom: 20px; }
.card-header { color: #409eff; font-weight: 700; }
.step-form { background: #f8f9fa; padding: 24px; border-radius: 8px; border: 1px solid #e4e7ed; }
.step-actions { display: flex; justify-content: space-between; margin-top: 20px; }
</style>
