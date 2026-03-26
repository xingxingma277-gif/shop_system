<template>
  <div class="step-container">
    <h3 class="step-title">第四步：确认订单</h3>

    <el-card shadow="never" class="summary-card">
      <template #header>
        <div class="card-header">订单信息</div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="单据类型">
          <el-tag :type="wizardStore.orderType === 'quote' ? 'warning' : 'primary'">{{ orderTypeText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ wizardStore.customerInfo?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="拿货人">{{ wizardStore.buyerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="项目">{{ wizardStore.project || '无' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ wizardStore.remark || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="items-card">
      <template #header>
        <div class="card-header">商品清单</div>
      </template>
      <el-table :data="wizardStore.items" border>
        <el-table-column prop="product_name" label="商品" min-width="180" />
        <el-table-column prop="spec" label="规格" width="120" />
        <el-table-column prop="unit" label="单位" width="90" />
        <el-table-column prop="qty" label="数量" width="100" />
        <el-table-column label="单价" width="120">
          <template #default="{ row }">¥ {{ Number(row.actual_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="小计" width="130">
          <template #default="{ row }">¥ {{ (Number(row.qty || 0) * Number(row.actual_price || 0)).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" />
      </el-table>
      <div class="total-box">总金额：<span>¥ {{ Number(wizardStore.totalAmount || 0).toFixed(2) }}</span></div>
    </el-card>

    <div class="step-actions">
      <el-button size="large" @click="goPrev">返回修改商品</el-button>
      <el-button type="primary" size="large" @click="goNext" :loading="submittingQuote">
        {{ wizardStore.orderType === 'quote' ? '提交报价单' : '去结算' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createSale } from '../../../api/sales'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useSaleWizardDraft } from '../../../composables/useSaleWizardDraft'

const router = useRouter()
const wizardStore = useSaleWizardStore()
const { save } = useSaleWizardDraft(wizardStore)
const submittingQuote = ref(false)
const orderTypeText = computed(() => (wizardStore.orderType === 'quote' ? '报价单' : '销售单'))

const goPrev = () => {
  wizardStore.setCurrentStep(3)
  save()
  router.push('/sales/wizard/step3')
}

const submitQuote = async () => {
  try {
    await ElMessageBox.confirm('确认提交报价单？', '提交确认', { type: 'warning' })
    submittingQuote.value = true

    const payload = {
      customer_id: wizardStore.customerInfo.id,
      buyer_id: wizardStore.buyerId,
      order_stage: 'QUOTE',
      order_type: 'quote',
      project: wizardStore.project || null,
      note: wizardStore.remark || null,
      settlement_status: 'UNPAID',
      paid_amount: 0,
      payment_method: null,
      payment_note: null,
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
    ElMessage.success('报价单提交成功')
    router.push(`/sales/${sale.id}?from_submit=1`)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error?.response?.data?.detail || '报价单提交失败')
  } finally {
    submittingQuote.value = false
  }
}


onMounted(() => {
  if (!wizardStore.customerInfo || wizardStore.items.length === 0) {
    ElMessage.warning('请先完成前序开单步骤')
    router.push('/sales/wizard/step1')
  }
})

const goNext = async () => {
  if (wizardStore.orderType === 'quote') {
    await submitQuote()
    return
  }

  wizardStore.setCurrentStep(5)
  save()
  router.push('/sales/wizard/step5')
}
</script>

<style scoped>
.step-container { max-width: 1100px; margin: 0 auto; padding-top: 10px; }
.step-title { text-align: center; margin-bottom: 20px; color: #303133; font-weight: 600; }
.summary-card, .items-card { margin-bottom: 16px; }
.card-header { font-weight: 700; color: #409eff; }
.total-box { text-align: right; margin-top: 16px; font-size: 16px; }
.total-box span { color: #f56c6c; font-weight: 700; font-size: 22px; }
.step-actions { display: flex; justify-content: space-between; margin-top: 16px; }
</style>
