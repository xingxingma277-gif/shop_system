<template>
  <el-result icon="info" title="开单流程已迁移" sub-title="正在跳转到新版开单向导..." />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
onMounted(() => {
  router.replace('/sales/wizard/step1')
})
</script>
