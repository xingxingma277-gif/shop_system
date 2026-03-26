<template>
  <div class="step-container">
    <h3 class="step-title">第四步：结算确认与生成单据</h3>

    <el-card shadow="never" class="summary-card">
      <template #header>
        <div class="card-header">
          <span>最终订单摘要</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="客户名称">{{ wizardStore.customerInfo?.name }}</el-descriptions-item>
        <el-descriptions-item label="业务类型">
          <el-tag :type="wizardStore.orderType === 'retail' ? 'primary' : 'warning'">
            {{ wizardStore.orderType === 'retail' ? '直接销售单' : '报价单' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="拿货人" v-if="buyerName">{{ buyerName }}</el-descriptions-item>
        <el-descriptions-item label="项目/备注">{{ wizardStore.projectRemarks || '无' }}</el-descriptions-item>
        <el-descriptions-item label="商品种类数">{{ wizardStore.items.length }} 种</el-descriptions-item>
        <el-descriptions-item label="订单总额">
          <span class="highlight-amount">¥ {{ (wizardStore.totalAmount || 0).toFixed(2) }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-form label-width="120px" class="step-form" v-if="wizardStore.orderType === 'retail'">
      <el-form-item label="结算方式">
        <el-radio-group v-model="formData.settlement_status" @change="handleStatusChange">
          <el-radio-button label="UNPAID">未付款 (挂账)</el-radio-button>
          <el-radio-button label="PARTIAL">部分付款 (首付)</el-radio-button>
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

      <el-form-item label="付款途径" v-if="formData.settlement_status !== 'UNPAID'">
        <el-select v-model="formData.payment_method" style="width: 200px;">
          <el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
        </el-select>
      </el-form-item>

      <el-form-item label="资金备注" v-if="formData.settlement_status !== 'UNPAID'">
        <el-input v-model="formData.payment_note" placeholder="例如：微信转账截图已留存..." />
      </el-form-item>
    </el-form>

    <div class="step-actions">
      <el-button size="large" @click="goPrev" :disabled="isSubmitting">返回修改商品</el-button>
      <el-button type="success" size="large" @click="submitOrder" :loading="isSubmitting">
        确认无误，生成单据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useCatalogStore } from '../../../stores/catalog'
import { useDictsStore } from '../../../stores/dicts'
import { createSale } from '../../../api/sales'

const router = useRouter()
const wizardStore = useSaleWizardStore()
const catalog = useCatalogStore()
const dicts = useDictsStore()

const isSubmitting = ref(false)
const paymentMethods = computed(() => dicts.paymentMethods)

// 尝试从本地找一下拿货人名字显示在小票上
const buyerName = computed(() => {
  if (!wizardStore.buyerId) return null
  // 注意：真实场景中这里可能由于数据没加载全显示不出，不影响业务
  return catalog.customers.find(c => c.id === wizardStore.customerInfo?.id)?.name || '指定拿货人'
})

const formData = reactive({
  settlement_status: 'PAID',
  paid_amount: wizardStore.totalAmount || 0,
  payment_method: 'bank_transfer',
  payment_note: ''
})

const handleStatusChange = (val) => {
  if (val === 'UNPAID') {
    formData.paid_amount = 0
  } else if (val === 'PAID') {
    formData.paid_amount = wizardStore.totalAmount
  } else {
    // 切换到部分付款时，如果本来是0或者全款，清空让用户重新填
    if (formData.paid_amount === 0 || formData.paid_amount === wizardStore.totalAmount) {
      formData.paid_amount = 0
    }
  }
}

const goPrev = () => {
  router.push('/sales/wizard/step3')
}

const submitOrder = async () => {
  if (wizardStore.orderType === 'retail' && formData.settlement_status !== 'UNPAID' && !formData.payment_method) {
    return ElMessage.warning('请选择收款途径')
  }

  try {
    await ElMessageBox.confirm('确认信息无误并生成单据吗？生成后不可直接修改。', '操作提示', { type: 'warning' })
    isSubmitting.value = true

    // 组装最终发给后端的庞大 JSON
    const payload = {
      customer_id: wizardStore.customerInfo.id,
      buyer_id: wizardStore.buyerId,
      order_stage: wizardStore.orderType === 'quote' ? 'QUOTE' : 'SALE_CONFIRMED',
      order_type: wizardStore.orderType === 'quote' ? 'quote' : 'sale_direct',
      project: wizardStore.projectRemarks,

      // 付款信息 (仅零售单传)
      settlement_status: wizardStore.orderType === 'retail' ? formData.settlement_status : 'UNPAID',
      paid_amount: wizardStore.orderType === 'retail' ? formData.paid_amount : 0,
      payment_method: wizardStore.orderType === 'retail' && formData.settlement_status !== 'UNPAID' ? formData.payment_method : null,
      payment_note: wizardStore.orderType === 'retail' ? formData.payment_note : null,

      // 商品明细
      items: wizardStore.items.map(item => ({
        product_id: item.product_id,
        qty: item.qty,
        unit_price: item.actual_price,
        note: item.remark || null
      }))
    }

    const sale = await createSale(payload)

    ElMessage.success('开单成功！')
    wizardStore.clearDraft() // 打扫战场

    // 跳去详情页欣赏一下自己的杰作
    router.push(`/sales/${sale.id}`)

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || error?.message || '生成单据失败')
    }
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  if (!wizardStore.customerInfo || wizardStore.items.length === 0) {
    ElMessage.warning('检测到开单数据丢失，请重新走流程')
    router.push('/sales/wizard/step1')
    return
  }
  formData.paid_amount = wizardStore.totalAmount
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