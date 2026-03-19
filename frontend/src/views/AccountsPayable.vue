<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>应付管理</b><el-button type="primary" @click="openPayDialog">新增付款</el-button></div></template>

    <div style="display:flex;gap:8px;margin-bottom:10px;">
      <el-select v-model="supplierId" filterable placeholder="选择供应商" style="width:260px" @change="loadAll">
        <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </div>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>未结采购单</b></template>
          <el-table :data="openPurchases" border size="small">
            <el-table-column prop="purchase_no" label="采购单号" min-width="130" />
            <el-table-column prop="total_amount" label="总额" width="90" />
            <el-table-column prop="paid_amount" label="已付" width="90" />
            <el-table-column prop="ap_amount" label="应付" width="90" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>付款记录</b></template>
          <el-table :data="paymentRecords" border size="small">
            <el-table-column prop="receipt_no" label="付款单号" min-width="140" />
            <el-table-column prop="amount" label="付款" width="80" />
            <el-table-column prop="allocated_amount" label="已核销" width="90" />
            <el-table-column prop="remain_amount" label="未分配" width="90" />
            <el-table-column label="操作" width="90"><template #default="{row}"><el-button link type="primary" @click="openAllocate(row)">核销</el-button></template></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-card>

  <el-dialog v-model="payDialog" title="新增供应商付款" width="500px">
    <el-form label-width="90px">
      <el-form-item label="付款方式">
        <el-select v-model="payForm.method" style="width:220px"><el-option v-for="m in paymentMethods" :key="m.value" :label="m.label" :value="m.value" /></el-select>
      </el-form-item>
      <el-form-item label="付款金额"><el-input-number v-model="payForm.amount" :min="0.01" /></el-form-item>
      <el-form-item label="备注"><el-input v-model="payForm.note" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="payDialog=false">取消</el-button><el-button type="primary" @click="submitPay">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="allocDialog" title="付款核销" width="620px">
    <el-table :data="allocRows" border>
      <el-table-column prop="purchase_no" label="采购单号" min-width="140" />
      <el-table-column prop="ap_amount" label="应付" width="100" />
      <el-table-column label="本次核销" width="160"><template #default="{row}"><el-input-number v-model="row.allocate_amount" :min="0" :max="row.ap_amount" /></template></el-table-column>
    </el-table>
    <template #footer><el-button @click="allocDialog=false">取消</el-button><el-button type="primary" @click="submitAllocate">确认核销</el-button></template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listSuppliers } from '../api/suppliers'
import { allocateSupplierPayment, createSupplierPayment, listSupplierOpenPurchases, listSupplierPaymentRecords } from '../api/purchase_payments'
import { useDictsStore } from '../stores/dicts'

const dicts = useDictsStore()
const paymentMethods = computed(() => dicts.paymentMethods)

const suppliers = ref([])
const supplierId = ref(null)
const openPurchases = ref([])
const paymentRecords = ref([])

const payDialog = ref(false)
const payForm = reactive({ method: 'bank_transfer', amount: 0, note: '' })

const allocDialog = ref(false)
const allocPaymentId = ref(null)
const allocRows = ref([])

async function loadAll() {
  if (!supplierId.value) {
    openPurchases.value = []
    paymentRecords.value = []
    return
  }
  openPurchases.value = await listSupplierOpenPurchases(supplierId.value)
  const p = await listSupplierPaymentRecords(supplierId.value)
  paymentRecords.value = p.items || []
}

function openPayDialog() {
  if (!supplierId.value) return ElMessage.warning('请先选择供应商')
  payForm.method = 'bank_transfer'
  payForm.amount = 0
  payForm.note = ''
  payDialog.value = true
}

async function submitPay() {
  try {
    await createSupplierPayment({ supplier_id: supplierId.value, amount: Number(payForm.amount || 0), method: payForm.method, note: payForm.note || null })
    ElMessage.success('付款已记录')
    payDialog.value = false
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

function openAllocate(row) {
  allocPaymentId.value = row.id
  allocRows.value = openPurchases.value.map((x) => ({ ...x, allocate_amount: 0 }))
  allocDialog.value = true
}

async function submitAllocate() {
  const items = allocRows.value.filter((x) => Number(x.allocate_amount) > 0).map((x) => ({ purchase_id: x.purchase_id, amount: Number(x.allocate_amount) }))
  if (!items.length) return ElMessage.warning('请填写核销金额')
  try {
    await allocateSupplierPayment(allocPaymentId.value, { items })
    ElMessage.success('核销完成')
    allocDialog.value = false
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '核销失败')
  }
}

onMounted(async () => {
  suppliers.value = await listSuppliers({ status: 'ACTIVE' })
})
</script>
