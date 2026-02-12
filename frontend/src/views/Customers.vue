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
      <el-table-column prop="phone" label="电话" width="160" />
      <el-table-column prop="address" label="地址" min-width="240" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goProfile(row)">档案</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:12px;">
      <el-pagination
        layout="prev, pager, next, sizes, total"
        :total="total"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        @current-change="fetchList"
        @size-change="fetchList"
      />
    </div>

    <el-dialog v-model="dialogOpen" :title="editing ? '编辑客户' : '新增客户'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogOpen=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ editing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listCustomers, createCustomer, updateCustomer } from '../api/customers'

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

const form = reactive({
  name: '',
  phone: '',
  address: '',
  is_active: true
})

function resetForm() {
  form.name = ''
  form.phone = ''
  form.address = ''
  form.is_active = true
}

async function fetchList() {
  const res = await listCustomers({
    page: page.value,
    page_size: pageSize.value,
    q: q.value || null,
    active_only: false
  })
  rows.value = res.items
  total.value = res.total
}

function openCreate() {
  editing.value = false
  editId.value = null
  resetForm()
  dialogOpen.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.name = row.name
  form.phone = row.phone || ''
  form.address = row.address || ''
  form.is_active = !!row.is_active
  dialogOpen.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入客户名称')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateCustomer(editId.value, {
        name: form.name,
        phone: form.phone || null,
        address: form.address || null,
        is_active: form.is_active
      })
      ElMessage.success('保存成功')
    } else {
      await createCustomer({
        name: form.name,
        phone: form.phone || null,
        address: form.address || null,
        is_active: form.is_active
      })
      ElMessage.success('创建成功')
    }
    dialogOpen.value = false
    await fetchList()
  } finally {
    saving.value = false
  }
}

function goProfile(row) {
  router.push(`/customers/${row.id}`)
}

onMounted(fetchList)
</script>
