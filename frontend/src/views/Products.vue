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
      <el-table-column label="标准价" width="120">
        <template #default="{ row }"><span class="money">¥{{ money(row.standard_price) }}</span></template>
      </el-table-column>
      <el-table-column label="成本价" width="120"><template #default="{ row }"><span class="money">¥{{ money(row.standard_cost || 0) }}</span></template></el-table-column>
      <el-table-column label="库存" width="120"><template #default="{ row }"><span :style="{color: Number(row.stock_quantity||0) <= Number(row.stock_warning_threshold||0) ? '#d4380d' : 'inherit'}">{{ row.stock_quantity }}</span></template></el-table-column>
      <el-table-column label="预警" width="100"><template #default="{ row }">{{ row.stock_warning_threshold || 0 }}</template></el-table-column>
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
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除该商品？删除后不可恢复。" @confirm="removeProduct(row)">
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
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
        <el-form-item label="成本价">
          <el-input-number v-model="form.standard_cost" :min="0" :step="1" />
        </el-form-item>
        <el-form-item label="库存数量">
          <el-input-number v-model="form.stock_quantity" :step="1" />
        </el-form-item>
        <el-form-item label="预警阈值">
          <el-input-number v-model="form.stock_warning_threshold" :min="0" :step="1" />
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

import { listProducts, createProduct, updateProduct, toggleProductActive, deleteProduct } from '../api/products'
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
  standard_price: 0,
  standard_cost: 0,
  stock_quantity: 0,
  stock_warning_threshold: 0
})

function resetForm() {
  form.name = ''
  form.sku = ''
  form.unit = ''
  form.standard_price = 0
  form.standard_cost = 0
  form.stock_quantity = 0
  form.stock_warning_threshold = 0
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
  form.standard_cost = Number(row.standard_cost || 0)
  form.stock_quantity = Number(row.stock_quantity || 0)
  form.stock_warning_threshold = Number(row.stock_warning_threshold || 0)
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
        standard_price: Number(form.standard_price || 0),
        standard_cost: Number(form.standard_cost || 0),
        stock_quantity: Number(form.stock_quantity || 0),
        stock_warning_threshold: Number(form.stock_warning_threshold || 0)
      })
      ElMessage.success('保存成功')
    } else {
      await createProduct({
        name: form.name,
        sku: form.sku || null,
        unit: form.unit || null,
        standard_price: Number(form.standard_price || 0),
        standard_cost: Number(form.standard_cost || 0),
        stock_quantity: Number(form.stock_quantity || 0),
        stock_warning_threshold: Number(form.stock_warning_threshold || 0),
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
  const updated = await toggleProductActive(row.id)
  Object.assign(row, updated)
}

async function removeProduct(row) {
  try {
    await deleteProduct(row.id)
    ElMessage.success('商品删除成功')
    await fetchList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchList)
</script>
