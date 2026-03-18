<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <b>采购单详情</b>
        <el-button @click="router.push('/purchases')">返回采购列表</el-button>
      </div>
    </template>

    <el-descriptions v-if="detail" :column="2" border>
      <el-descriptions-item label="采购单号">{{ detail.purchase_no }}</el-descriptions-item>
      <el-descriptions-item label="状态">{{ detail.status }}</el-descriptions-item>
      <el-descriptions-item label="供应商">{{ detail.supplier_name }}</el-descriptions-item>
      <el-descriptions-item label="仓库">{{ detail.warehouse_name }}</el-descriptions-item>
      <el-descriptions-item label="总金额">{{ detail.total_amount }}</el-descriptions-item>
      <el-descriptions-item label="应付">{{ detail.ap_amount }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ detail.note || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-table v-if="detail" :data="detail.items || []" border style="margin-top:12px;">
      <el-table-column prop="product_name" label="商品" min-width="180" />
      <el-table-column prop="qty" label="采购数量" width="110" />
      <el-table-column prop="received_qty" label="已入库" width="110" />
      <el-table-column prop="unit_cost" label="单价" width="100" />
      <el-table-column prop="line_total" label="金额" width="100" />
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPurchase } from '../api/purchases'

const route = useRoute()
const router = useRouter()
const detail = ref(null)

onMounted(async () => {
  detail.value = await getPurchase(route.params.id)
})
</script>
