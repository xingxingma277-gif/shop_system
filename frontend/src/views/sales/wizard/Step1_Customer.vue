<template>
  <div class="step-container">
    <h3 class="step-title">第一步：请选择业务类型</h3>

    <div class="type-cards">
      <el-card
        :class="['type-card', formData.orderType === 'retail' ? 'active' : '']"
        @click="selectType('retail')"
        shadow="hover"
      >
        <div class="card-icon">🛒</div>
        <h4>直接销售单</h4>
        <p>确认后将直接扣减仓库实际库存，并生成财务应收账款。</p>
      </el-card>

      <el-card
        :class="['type-card', formData.orderType === 'quote' ? 'active' : '']"
        @click="selectType('quote')"
        shadow="hover"
      >
        <div class="card-icon">📄</div>
        <h4>生成报价单</h4>
        <p>仅用于给客户提供价格明细，不会扣减库存，后续可转为销售单。</p>
      </el-card>
    </div>

    <div class="step-actions" style="justify-content: center; margin-top: 40px;">
      <el-button type="primary" size="large" @click="goNext" style="width: 200px;">
        下一步：填写客户信息
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useSaleWizardStore } from '../../../stores/saleWizard'

const router = useRouter()
const wizardStore = useSaleWizardStore()

const formData = reactive({
  orderType: wizardStore.orderType || 'retail'
})

const selectType = (type) => {
  formData.orderType = type
}

const goNext = () => {
  wizardStore.orderType = formData.orderType
  router.push('/sales/wizard/step2')
}
</script>

<style scoped>
.step-container { max-width: 800px; margin: 0 auto; padding-top: 40px; }
.step-title { text-align: center; margin-bottom: 40px; color: #303133; font-weight: 600; }
.type-cards { display: flex; gap: 20px; justify-content: center; }
.type-card { flex: 1; cursor: pointer; text-align: center; border: 2px solid transparent; transition: all 0.3s; }
.type-card.active { border-color: #409eff; background-color: #ecf5ff; }
.card-icon { font-size: 48px; margin-bottom: 16px; }
.type-card h4 { margin: 0 0 8px 0; font-size: 18px; color: #303133; }
.type-card p { margin: 0; font-size: 13px; color: #909399; line-height: 1.5; }
</style>