<template>
  <div class="step-container">
    <h3 class="step-title">第四步：收款与提交</h3>

    <el-card shadow="never" class="summary-card">
      <template #header>
        <div class="card-header">
          <span>订单摘要</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="客户名称">{{ wizardStore.customerInfo?.name }}</el-descriptions-item>
        <el-descriptions-item label="单据类型">
          <el-tag :type="wizardStore.orderType === 'retail' ? 'primary' : 'warning'">
            {{ orderTypeText }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="拿货人" v-if="wizardStore.buyerName">{{ wizardStore.buyerName }}</el-descriptions-item>
        <el-descriptions-item label="项目">{{ wizardStore.project || '无' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ wizardStore.remark || '无' }}</el-descriptions-item>
        <el-descriptions-item label="商品种类数">{{ wizardStore.items.length }} 种</el-descriptions-item>
        <el-descriptions-item label="订单总额">
          <span class="highlight-amount">¥ {{ (wizardStore.totalAmount || 0).toFixed(2) }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-form label-width="120px" class="step-form" v-if="wizardStore.orderType === 'retail'">
      <el-form-item label="结算方式">
        <el-radio-group v-model="formData.settlement_status" @change="handleStatusChange">
          <el-radio-button label="UNPAID">未付款（挂账）</el-radio-button>
          <el-radio-button label="PARTIAL">部分付款（首付）</el-radio-button>
          <el-radio-button label="PAID">已付清</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="实收金额" v-if="formData.settlement_status !== 'UNPAID'">
        <el-input-number
          v-model="formData.paid_amount"
          :min="0"
          :max="wizardStore.totalAmount"
          :precision="2"
          :step="100"
          :disabled="formData.settlement_status === 'PAID'"
          style="width: 200px;"
        />
        <span class="help-text">范围: 0 ~ ¥{{ (wizardStore.totalAmount || 0).toFixed(2) }}</span>
      </el-form-item>

      <el-form-item label="付款方式" v-if="formData.settlement_status !== 'UNPAID'">
        <el-select v-model="formData.payment_method" style="width: 200px;">
          <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
        </el-select>
      </el-form-item>

      <el-form-item label="收款备注" v-if="formData.settlement_status !== 'UNPAID'">
        <el-input v-model="formData.payment_note" placeholder="例如：已核对转账凭证" />
      </el-form-item>
    </el-form>

    <div class="step-actions">
      <el-button size="large" @click="goPrev" :disabled="isSubmitting">返回添加商品</el-button>
      <el-button type="success" size="large" @click="submitOrder" :loading="isSubmitting">
        确认提交
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useDictsStore } from '../../../stores/dicts'
import { useSaleWizardDraft } from '../../../composables/useSaleWizardDraft'
import { createSale } from '../../../api/sales'

const router = useRouter()
const wizardStore = useSaleWizardStore()
const dicts = useDictsStore()
const { save } = useSaleWizardDraft(wizardStore)

const isSubmitting = ref(false)
const paymentMethods = computed(() => dicts.paymentMethods)
const orderTypeText = computed(() => (wizardStore.orderType === 'quote' ? '报价单' : '销售单'))

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
    wizardStore.setCurrentStep(4)
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
  wizardStore.setCurrentStep(3)
  save()
  router.push('/sales/wizard/step3')
}

const submitOrder = async () => {
  if (wizardStore.orderType === 'retail' && formData.settlement_status !== 'UNPAID' && !formData.payment_method) {
    return ElMessage.warning('请选择付款方式')
  }

  try {
    await ElMessageBox.confirm('确认提交当前销售单据吗？', '提交确认', { type: 'warning' })
    isSubmitting.value = true

    const payload = {
      customer_id: wizardStore.customerInfo.id,
      buyer_id: wizardStore.buyerId,
      order_stage: wizardStore.orderType === 'quote' ? 'QUOTE' : 'SALE_CONFIRMED',
      order_type: wizardStore.orderType === 'quote' ? 'quote' : 'sale_direct',
      project: wizardStore.project || null,
      note: wizardStore.remark || null,
      settlement_status: wizardStore.orderType === 'retail' ? formData.settlement_status : 'UNPAID',
      paid_amount: wizardStore.orderType === 'retail' ? formData.paid_amount : 0,
      payment_method: wizardStore.orderType === 'retail' && formData.settlement_status !== 'UNPAID' ? formData.payment_method : null,
      payment_note: wizardStore.orderType === 'retail' ? formData.payment_note : null,
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
    ElMessage.success('开单成功')
    router.push(`/sales/${sale.id}?from_submit=1`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || error?.message || '提交失败')
    }
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  if (!wizardStore.customerInfo || wizardStore.items.length === 0) {
    ElMessage.warning('开单数据不完整，请从第一步重新开始')
    router.push('/sales/wizard/step1')
    return
  }
  if (formData.settlement_status === 'PAID') {
    formData.paid_amount = wizardStore.totalAmount
  }
})
</script>

<style scoped>
.step-container { max-width: 800px; margin: 0 auto; padding-top: 20px; }
.step-title { margin-bottom: 20px; color: #303133; font-weight: 600; text-align: center; }
.summary-card { margin-bottom: 30px; border-radius: 8px; border: 1px solid #ebeef5; }
.card-header { font-weight: bold; color: #409eff; }
.highlight-amount { color: #f56c6c; font-size: 20px; font-weight: bold; }
.step-form { background: #f8f9fa; padding: 30px; border-radius: 8px; border: 1px solid #e4e7ed; margin-bottom: 30px; }
.help-text { margin-left: 12px; color: #909399; font-size: 13px; }
.step-actions { display: flex; justify-content: space-between; border-top: 1px solid #ebeef5; padding-top: 20px; }
</style>
