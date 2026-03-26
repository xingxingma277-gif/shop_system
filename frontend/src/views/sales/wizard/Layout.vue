<template>
  <div class="wizard-layout">
    <el-card shadow="never" class="wizard-header">
      <el-steps :active="currentStepIndex" finish-status="success" align-center>
        <el-step title="单据类型" />
        <el-step title="客户信息" />
        <el-step title="商品信息" />
        <el-step title="收款提交" />
      </el-steps>
    </el-card>

    <div class="wizard-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useSaleWizardStore } from '../../../stores/saleWizard'

const route = useRoute()
const router = useRouter()
const wizardStore = useSaleWizardStore()
const promptHandled = ref(false)

const stepMap = { step1: 0, step2: 1, step3: 2, step4: 3 }
const currentStepIndex = computed(() => {
  const pathNode = route.path.split('/').pop()
  return stepMap[pathNode] || 0
})

const updateStepByRoute = () => {
  wizardStore.setCurrentStep(currentStepIndex.value + 1)
}

watch(() => route.path, updateStepByRoute, { immediate: true })

onMounted(async () => {
  wizardStore.loadDraftFromLocal()

  const isStep1 = route.path.endsWith('/sales/wizard/step1') || route.path.endsWith('/step1')
  if (!isStep1 || promptHandled.value || !wizardStore.hasMeaningfulDraft()) {
    return
  }

  promptHandled.value = true

  try {
    await ElMessageBox.confirm('检测到您有未提交的开单草稿，是否继续之前的开单流程？', '恢复开单草稿', {
      confirmButtonText: '继续开单',
      cancelButtonText: '重新开单',
      distinguishCancelAndClose: true,
      type: 'info'
    })

    const target = `/sales/wizard/step${wizardStore.currentStep || 1}`
    if (target !== route.path) {
      router.replace(target)
    }
  } catch (error) {
    wizardStore.clearDraft()
  }
})

onBeforeRouteLeave(async (to) => {
  if (to.path.startsWith('/sales/wizard')) {
    return true
  }

  if (wizardStore.isSubmitted || !wizardStore.hasMeaningfulDraft()) {
    return true
  }

  try {
    await ElMessageBox.confirm('当前开单信息尚未提交，离开后可稍后继续。确认离开当前页面吗？', '离开确认', {
      confirmButtonText: '确认离开',
      cancelButtonText: '继续编辑',
      type: 'warning'
    })
    return true
  } catch (error) {
    return false
  }
})
</script>

<style scoped>
.wizard-layout { display: flex; flex-direction: column; gap: 16px; height: 100%; }
.wizard-header { flex-shrink: 0; }
.wizard-content { flex: 1; overflow: auto; background: #fff; border-radius: 4px; padding: 24px; border: 1px solid #ebeef5; }
</style>
