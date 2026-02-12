<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <div style="font-weight:700;">商品管理</div>
        <div>
          <el-input v-model="q" placeholder="搜索商品名或SKU" style="width: 260px;" @keyup.enter="fetchList" />
          <el-button style="margin-left:8px;" @click="fetchList">搜索</el-button>
          <el-button type="primary" style="margin-left:8px;" @click="openCreate">新增商品</el-button>
        </div>
      </div>
    </template>

    <el-table :data="rows" border>
      <el-table-column prop="name" label="名称" min-width="220" />
      <el-table-column prop="sku" label="SKU" width="160" />
      <el-table-column prop="unit" label="单位" width="100" />
      <el-table-column label="标准价" width="140">
        <template #default="{ row }"><span class="money">¥{{ money(row.standard_price) }}</span></template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            active-text="启用"
            inactive-text="停用"
            @change="()=>toggle(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
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

    <el-dialog v-model="dialogOpen" :title="editing ? '编辑商品' : '新增商品'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="SKU">
          <el-input v-model="form.sku" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" />
        </el-form-item>
        <el-form-item label="标准价" required>
          <el-input-number v-model="form.standard_price" :min="0" :step="1" />
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
import { ElMessage } from 'element-plus'

import { listProducts, createProduct, updateProduct, toggleProductActive } from '../api/products'
import { money } from '../utils/format'

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
  sku: '',
  unit: '',
  standard_price: 0
})

function resetForm() {
  form.name = ''
  form.sku = ''
  form.unit = ''
  form.standard_price = 0
}

async function fetchList() {
  const res = await listProducts({
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
  form.sku = row.sku || ''
  form.unit = row.unit || ''
  form.standard_price = Number(row.standard_price || 0)
  dialogOpen.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入商品名称')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateProduct(editId.value, {
        name: form.name,
        sku: form.sku || null,
        unit: form.unit || null,
        standard_price: Number(form.standard_price || 0)
      })
      ElMessage.success('保存成功')
    } else {
      await createProduct({
        name: form.name,
        sku: form.sku || null,
        unit: form.unit || null,
        standard_price: Number(form.standard_price || 0),
        is_active: true
      })
      ElMessage.success('创建成功')
    }
    dialogOpen.value = false
    await fetchList()
  } finally {
    saving.value = false
  }
}

async function toggle(row) {
  // 后端是 toggle_active：因此这里直接调用接口并用返回值覆盖
  const updated = await toggleProductActive(row.id)
  Object.assign(row, updated)
}

onMounted(fetchList)
</script>
