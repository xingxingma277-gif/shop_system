<template>
  <div class="wizard-layout">
    <el-card shadow="never" class="wizard-header">
      <el-steps :active="currentStepIndex" finish-status="success" align-center>
        <el-step title="业务类型" description="销售或报价" />
        <el-step title="客户信息" description="客户与拿货人" />
        <el-step title="商品与核价" description="库存与历史价" />
        <el-step title="结算确认" description="生成最终单据" />
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const stepMap = { 'step1': 0, 'step2': 1, 'step3': 2, 'step4': 3 }
const currentStepIndex = computed(() => {
  const pathNode = route.path.split('/').pop()
  return stepMap[pathNode] || 0
})
</script>

<style scoped>
.wizard-layout { display: flex; flex-direction: column; gap: 16px; height: 100%; }
.wizard-header { flex-shrink: 0; }
.wizard-content { flex: 1; overflow: auto; background: #fff; border-radius: 4px; padding: 24px; border: 1px solid #ebeef5; }
</style>