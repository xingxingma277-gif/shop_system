<template>
  <el-card>
    <template #header><b>库存台账</b></template>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;">
      <el-select v-model="filters.warehouse_id" clearable placeholder="仓库" style="width:180px"><el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" /></el-select>
      <el-select v-model="filters.biz_type" clearable placeholder="业务类型" style="width:180px"><el-option label="销售出库" value="sale" /><el-option label="采购入库" value="purchase_receive" /><el-option label="采购退货" value="purchase_return" /><el-option label="库存调整" value="inventory_adjustment" /><el-option label="库存盘点" value="inventory_check" /><el-option label="调拨调出" value="inventory_transfer_out" /><el-option label="调拨调入" value="inventory_transfer_in" /></el-select>
      <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始" end-placeholder="结束" />
      <el-button type="primary" @click="load">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="created_at" label="时间" min-width="170" />
      <el-table-column prop="warehouse_name" label="仓库" width="120" />
      <el-table-column prop="product_name" label="商品" min-width="160" />
      <el-table-column prop="change_qty" label="变动" width="100" />
      <el-table-column prop="after_qty" label="结存" width="100" />
      <el-table-column prop="biz_type" label="业务类型" width="140" />
      <el-table-column prop="note" label="备注" min-width="200" />
    </el-table>
  </el-card>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { listWarehouses } from '../api/warehouses'
import { listInventoryLedger } from '../api/inventory'

const rows = ref([])
const warehouses = ref([])
const filters = reactive({ warehouse_id: null, biz_type: '', dateRange: [] })

async function load() {
  const data = await listInventoryLedger({
    warehouse_id: filters.warehouse_id || undefined,
    biz_type: filters.biz_type || undefined,
    start_date: filters.dateRange?.[0] ? dayjs(filters.dateRange[0]).toISOString() : undefined,
    end_date: filters.dateRange?.[1] ? dayjs(filters.dateRange[1]).toISOString() : undefined,
  })
  rows.value = data.items || []
}

onMounted(async () => {
  warehouses.value = await listWarehouses({})
  await load()
})
</script>
