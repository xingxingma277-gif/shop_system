<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <div style="display:flex;align-items:center;gap:8px;">
          <div style="font-weight:700;">商品管理</div>
          <el-button v-if="backLabel" link type="primary" @click="backToOrigin">{{ backLabel }}</el-button>
        </div>
        <div>
          <el-input v-model="q" placeholder="搜索商品名或SKU" style="width: 260px;" @keyup.enter="fetchList" />
          <el-button style="margin-left:8px;" @click="fetchList">搜索</el-button>
          <el-button type="primary" style="margin-left:8px;" @click="openCreate">新增商品</el-button>
        </div>
      </div>
    </template>

    <el-alert v-if="contextMessage" :title="contextMessage" type="info" :closable="false" style="margin-bottom:12px;" />

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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { listProducts, createProduct, updateProduct, toggleProductActive, deleteProduct } from '../api/products'
import { money } from '../utils/format'

const route = useRoute()
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

const backLabel = computed(() => route.query.return_to === 'inventory-ledger' ? '返回库存台账' : '')
const contextMessage = computed(() => {
  if (route.query.return_to !== 'inventory-ledger') return ''
  if (route.query.context === 'low_stock' && typeof route.query.product_name === 'string') {
    return `当前来自低库存台账，已按商品“${route.query.product_name}”定位到商品管理。`
  }
  return '当前来自库存台账上下文。'
})

function applyRouteQuery() {
  q.value = typeof route.query.q === 'string' ? route.query.q : ''
}

function backToOrigin() {
  if (route.query.return_to !== 'inventory-ledger') return
  const query = {}
  if (typeof route.query.product_id === 'string') query.product_id = route.query.product_id
  if (typeof route.query.product_name === 'string') query.product_name = route.query.product_name
  if (typeof route.query.warehouse_id === 'string') query.warehouse_id = route.query.warehouse_id
  if (typeof route.query.biz_type === 'string') query.biz_type = route.query.biz_type
  if (typeof route.query.preset === 'string') query.preset = route.query.preset
  if (typeof route.query.start_date === 'string') query.start_date = route.query.start_date
  if (typeof route.query.end_date === 'string') query.end_date = route.query.end_date
  if (typeof route.query.source === 'string') query.source = route.query.source
  if (typeof route.query.context === 'string') query.context = route.query.context
  router.push({ path: '/inventory-ledger', query })
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

watch(q, (value) => {
  const nextQuery = {}
  if (value) nextQuery.q = value
  for (const key of ['return_to', 'product_id', 'product_name', 'warehouse_id', 'biz_type', 'preset', 'start_date', 'end_date', 'source', 'context']) {
    if (typeof route.query[key] === 'string') nextQuery[key] = route.query[key]
  }
  if ((route.query.q || '') === (value || '')) return
  router.replace({ path: '/products', query: nextQuery })
})

watch(() => route.query.q, async () => {
  applyRouteQuery()
  await fetchList()
})

onMounted(async () => {
  applyRouteQuery()
  await fetchList()
})
</script>
