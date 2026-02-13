<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <div style="font-weight:700;">客户管理</div>
        <div>
          <el-input v-model="q" placeholder="搜索客户名" style="width: 260px;" @keyup.enter="fetchList" />
          <el-button style="margin-left:8px;" @click="fetchList">搜索</el-button>
          <el-button type="primary" style="margin-left:8px;" @click="openCreate">新增客户</el-button>
        </div>
      </div>
    </template>

    <el-table :data="rows" border>
      <el-table-column prop="name" label="名称" min-width="220" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="contact_name" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="160" />
      <el-table-column prop="address" label="地址" min-width="240" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '正常' : '停用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goProfile(row)">档案</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="openDeleteGuide(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:12px;">
      <el-pagination layout="prev, pager, next, sizes, total" :total="total" v-model:current-page="page" v-model:page-size="pageSize" @current-change="fetchList" @size-change="fetchList" />
    </div>

    <el-dialog v-model="dialogOpen" :title="editing ? '编辑客户' : '新增客户'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required><el-select v-model="form.type"><el-option label="公司" value="company" /><el-option label="个人" value="personal" /></el-select></el-form-item>
        <el-form-item label="联系人" required><el-input v-model="form.contact_name" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.is_active" active-text="正常" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">{{ editing ? '保存' : '创建' }}</el-button></template>
    </el-dialog>

    <el-dialog v-model="deleteDialog" title="无法直接删除：该客户存在交易记录" width="860px">
      <el-alert title="删除后不可恢复" type="error" :closable="false" style="margin-bottom:10px" />
      <div style="margin-bottom:8px">销售记录 {{ delInfo.sales_count }} 条，还款记录 {{ delInfo.payments_count }} 条</div>

      <el-collapse>
        <el-collapse-item title="销售记录" name="sales">
          <el-table :data="delInfo.sales || []" size="small" border @selection-change="(rows)=>selectedSaleIds = rows.map(x=>x.id)">
            <el-table-column v-if="selectMode" type="selection" width="48" />
            <el-table-column prop="sale_no" label="单号" min-width="140" />
            <el-table-column prop="created_at" label="时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.created_at) }}</template></el-table-column>
            <el-table-column prop="balance" label="未收" width="100" />
          </el-table>
        </el-collapse-item>
        <el-collapse-item title="还款记录" name="payments">
          <el-table :data="delInfo.payments || []" size="small" border @selection-change="(rows)=>selectedPaymentIds = rows.map(x=>x.id)">
            <el-table-column v-if="selectMode" type="selection" width="48" />
            <el-table-column prop="paid_at" label="时间" min-width="160"><template #default="{row}">{{ formatDateTime(row.paid_at) }}</template></el-table-column>
            <el-table-column prop="amount" label="金额" width="100" />
            <el-table-column prop="method" label="方式" width="100" />
            <el-table-column prop="sale_nos" label="关联订单" min-width="200"><template #default="{row}">{{ (row.sale_nos||[]).join('、') }}</template></el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>

      <template #footer>
        <el-button @click="deleteDialog=false">取消</el-button>
        <el-button @click="selectMode=true">选择删除</el-button>
        <el-button type="danger" :loading="deleting" @click="deleteAllAndCustomer">全部删除交易并删除客户</el-button>
        <el-button v-if="selectMode" type="danger" plain :loading="deleting" @click="deleteSelected">删除已选记录</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCustomer, deleteCustomer, deleteCustomerCheck, deleteCustomerRecords, listCustomers, updateCustomer } from '../api/customers'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const q = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const rows = ref([])

const dialogOpen = ref(false)
const saving = ref(false)
const editing = ref(false)
const editId = ref(null)
const form = reactive({ name: '', type: 'company', contact_name: '', phone: '', address: '', is_active: true })

const deleteDialog = ref(false)
const deleteCustomerId = ref(null)
const delInfo = reactive({ can_delete: false, sales_count: 0, payments_count: 0, sales: [], payments: [] })
const selectedSaleIds = ref([])
const selectedPaymentIds = ref([])
const selectMode = ref(false)
const deleting = ref(false)

function resetForm() { form.name=''; form.type='company'; form.contact_name=''; form.phone=''; form.address=''; form.is_active=true }

async function fetchList() {
  const res = await listCustomers({ page: page.value, page_size: pageSize.value, q: q.value || null, active_only: false })
  rows.value = res.items || []
  total.value = Number(res.meta?.total || 0)
}

function openCreate(){ editing.value=false; editId.value=null; resetForm(); dialogOpen.value=true }
function openEdit(row){ editing.value=true; editId.value=row.id; Object.assign(form,{name:row.name,type:row.type||'company',contact_name:row.contact_name||'',phone:row.phone||'',address:row.address||'',is_active:!!row.is_active}); dialogOpen.value=true }

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请输入客户名称')
  saving.value = true
  try {
    if (editing.value) await updateCustomer(editId.value, { ...form })
    else await createCustomer({ ...form })
    dialogOpen.value = false
    await fetchList()
  } finally { saving.value = false }
}

async function openDeleteGuide(row) {
  const check = await deleteCustomerCheck(row.id)
  if (check.can_delete) {
    await deleteCustomer(row.id)
    ElMessage.success('客户删除成功')
    return fetchList()
  }
  deleteCustomerId.value = row.id
  Object.assign(delInfo, check)
  selectedSaleIds.value = []
  selectedPaymentIds.value = []
  selectMode.value = false
  deleteDialog.value = true
}

async function deleteSelected() {
  if (!selectedSaleIds.value.length && !selectedPaymentIds.value.length) return ElMessage.warning('请选择要删除的交易记录')
  deleting.value = true
  try {
    await deleteCustomerRecords(deleteCustomerId.value, { sale_ids: selectedSaleIds.value, payment_ids: selectedPaymentIds.value })
    Object.assign(delInfo, await deleteCustomerCheck(deleteCustomerId.value))
    ElMessage.success('已删除选中记录')
    if (delInfo.can_delete) {
      await deleteCustomer(deleteCustomerId.value)
      deleteDialog.value = false
      await fetchList()
      ElMessage.success('客户删除成功')
    }
  } finally { deleting.value = false }
}

async function deleteAllAndCustomer() {
  await ElMessageBox.confirm('将删除该客户所有交易记录并删除客户，删除后不可恢复。是否继续？', '危险操作确认', { type: 'warning' })
  deleting.value = true
  try {
    await deleteCustomerRecords(deleteCustomerId.value, { sale_ids: (delInfo.sales || []).map(x => x.id), payment_ids: (delInfo.payments || []).map(x => x.id) })
    await deleteCustomer(deleteCustomerId.value)
    deleteDialog.value = false
    await fetchList()
    ElMessage.success('已删除交易并删除客户')
  } finally { deleting.value = false }
}

function goProfile(row) { router.push(`/customers/${row.id}`) }

onMounted(fetchList)
</script>
