<template>
  <div class="step-container">
    <el-alert
      v-if="wizardStore.orderType === 'quote'"
      title="当前为报价单，仅作报价参考，不会扣减库存。"
      type="info"
      show-icon
      style="margin-bottom: 20px;"
    />

    <div class="step-header">
      <h3 class="step-title">第三步：添加商品</h3>
      <el-button type="primary" plain @click="addRow">+ 添加商品</el-button>
    </div>

    <el-table
      :data="formData.items"
      border
      class="items-table"
      empty-text="请点击右上角添加商品"
      height="500"
      :row-class-name="tableRowClassName"
    >
      <el-table-column type="index" label="序号" width="60" align="center" fixed="left" />

      <el-table-column label="选择商品" min-width="240" fixed="left">
        <template #default="{ row, $index }">
          <el-select
            v-model="row.product_id"
            filterable
            remote
            :remote-method="onSearchProducts"
            placeholder="拼音/名称搜索"
            style="width: 100%;"
            @change="(val) => handleProductChange(val, row, $index)"
          >
            <el-option v-for="p in catalog.products" :key="p.id" :label="p.name" :value="p.id" :disabled="!p.is_active">
              <span style="float: left">{{ p.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px; margin-left: 20px;">
                库存: {{ p.stock_quantity }} {{ p.unit }}
              </span>
            </el-option>
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="规格" prop="spec" width="120">
        <template #default="{ row }">{{ row.spec || '-' }}</template>
      </el-table-column>

      <el-table-column label="单位" prop="unit" width="80" align="center">
        <template #default="{ row }">{{ row.unit || '-' }}</template>
      </el-table-column>

      <el-table-column label="库存" width="100" align="center">
        <template #default="{ row }">
          <span :class="{ 'stock-warning': wizardStore.orderType === 'retail' && row.qty > row.stock_quantity }">
            {{ row.stock_quantity ?? '-' }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="最近成交价" min-width="220">
        <template #default="{ row }">
          <div class="price-cell">
            <span v-if="row.loadingHistory" class="loading-text">查询中...</span>
            <template v-else-if="row.last_price !== null && row.last_price !== undefined">
              <span class="history-price">¥ {{ Number(row.last_price).toFixed(2) }}</span>
              <span class="history-sub">{{ row.last_sale_date ? formatDate(row.last_sale_date) : '时间未知' }} / {{ row.last_sale_no || '未知单号' }}</span>
              <span class="history-sub" v-if="row.standard_price !== null && row.standard_price !== undefined">标准价：¥ {{ Number(row.standard_price).toFixed(2) }}</span>
              <div>
                <el-button link type="success" @click="applyLastPrice(row)">采用最近成交价</el-button>
                <el-button link type="primary" @click="openHistoryDialog(row)">查看历史记录</el-button>
              </div>
            </template>
            <span v-else style="color: #c0c4cc;">暂无历史成交</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="数量" width="130">
        <template #default="{ row }">
          <el-input-number v-model="row.qty" :min="1" @change="calculateTotal" style="width: 100%;" />
        </template>
      </el-table-column>

      <el-table-column label="单价" width="130">
        <template #default="{ row }">
          <el-input-number v-model="row.actual_price" :min="0" :precision="2" :step="1" @change="calculateTotal" style="width: 100%;" />
        </template>
      </el-table-column>

      <el-table-column label="小计" width="130" align="right">
        <template #default="{ row }">
          <span class="highlight-amount">¥ {{ ((row.qty || 0) * (row.actual_price || 0)).toFixed(2) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="备注" min-width="160">
        <template #default="{ row }">
          <el-input v-model="row.remark" placeholder="本行说明（可选）" />
        </template>
      </el-table-column>

      <el-table-column label="操作" width="80" fixed="right" align="center">
        <template #default="{ $index }">
          <el-button type="danger" link @click="removeRow($index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="summary-section">
      <div class="summary-text">
        <span>整单金额：</span>
        <span class="total-amount">¥ {{ formData.totalAmount.toFixed(2) }}</span>
      </div>
    </div>

    <div class="step-actions">
      <el-button size="large" @click="goPrev">返回选择客户</el-button>
      <el-button type="primary" size="large" @click="goNext">下一步：确认订单</el-button>
    </div>

    <el-dialog v-model="historyDialog.visible" width="760px" :title="`历史成交记录 - ${historyDialog.productName || ''}`">
      <el-table :data="historyDialog.rows" border size="small" max-height="420">
        <el-table-column prop="sale_no" label="单号" min-width="140" />
        <el-table-column prop="sale_date" label="成交时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.sale_date || row.date) }}</template>
        </el-table-column>
        <el-table-column prop="order_type" label="单据类型" min-width="110">
          <template #default="{ row }">{{ row.order_type === 'quote' ? '报价单' : '销售单' }}</template>
        </el-table-column>
        <el-table-column prop="unit_price" label="成交价" width="120">
          <template #default="{ row }">¥ {{ Number(row.unit_price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="qty" label="数量" width="100" />
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button link type="success" @click="useHistoryPrice(row)">使用该价</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { reactive, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useCatalogStore } from '../../../stores/catalog'
import { useSaleWizardDraft } from '../../../composables/useSaleWizardDraft'
import { getLatestDealPrice, getPricingHistory } from '../../../api/pricing'

const router = useRouter()
const wizardStore = useSaleWizardStore()
const catalog = useCatalogStore()
const { save } = useSaleWizardDraft(wizardStore)

const highlightRowIndex = ref(-1)
const historyDialog = reactive({ visible: false, rows: [], productName: '' })

const formData = reactive({
  items: wizardStore.items.length > 0 ? wizardStore.items.map((item) => ({ ...item })) : [{ product_id: null, qty: 1, actual_price: 0 }],
  totalAmount: wizardStore.totalAmount || 0
})

watch(
  () => formData.items,
  () => {
    wizardStore.items = formData.items.map((item) => ({ ...item }))
    save()
  },
  { deep: true }
)

watch(
  () => formData.totalAmount,
  (val) => {
    wizardStore.totalAmount = val
    save()
  }
)

const tableRowClassName = ({ rowIndex }) => (rowIndex === highlightRowIndex.value ? 'duplicate-row-flash' : '')
const onSearchProducts = async (query) => catalog.searchProducts(query || '')
const formatDate = (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-')

const loadLatestPrice = async (row, productId) => {
  if (!wizardStore.customerInfo?.id) return
  const latest = await getLatestDealPrice({ customer_id: wizardStore.customerInfo.id, product_id: productId })
  if (!latest) {
    row.last_price = null
    row.last_sale_date = null
    row.last_sale_no = null
    row.source_order_type = null
    return
  }

  row.standard_price = latest.standard_price
  row.last_price = latest.last_price
  row.last_sale_date = latest.last_sale_date
  row.last_sale_no = latest.last_sale_no
  row.source_order_type = latest.source_order_type
  row.source_stage = latest.source_stage
}

const handleProductChange = async (productId, row, index) => {
  if (!productId) return

  const duplicateIndex = formData.items.findIndex((item, i) => i !== index && item.product_id === productId)
  if (duplicateIndex !== -1) {
    ElMessage.warning(`商品已在第 ${duplicateIndex + 1} 行，请直接调整原行数量。`)
    row.product_id = null
    highlightRowIndex.value = duplicateIndex

    setTimeout(() => {
      if (highlightRowIndex.value === duplicateIndex) highlightRowIndex.value = -1
    }, 3000)
    save()
    return
  }

  const product = catalog.products.find((p) => p.id === productId)
  if (product) {
    row.product_name = product.name
    row.spec = product.spec
    row.unit = product.unit
    row.stock_quantity = product.stock_quantity || 0
    row.actual_price = product.standard_price || 0
  }

  row.loadingHistory = true
  await loadLatestPrice(row, productId)
  row.loadingHistory = false

  calculateTotal()
  save()
}

const openHistoryDialog = async (row) => {
  if (!wizardStore.customerInfo?.id || !row.product_id) return
  const res = await getPricingHistory({ customer_id: wizardStore.customerInfo.id, product_id: row.product_id, page: 1, page_size: 30 })
  historyDialog.rows = res.items || []
  historyDialog.productName = row.product_name
  historyDialog.visible = true
}


const applyLastPrice = (row) => {
  if (row.last_price === null || row.last_price === undefined) return
  row.actual_price = Number(row.last_price)
  calculateTotal()
  save()
}

const useHistoryPrice = (historyRow) => {
  const target = formData.items.find((item) => item.product_name === historyDialog.productName)
  if (!target) return
  target.actual_price = Number(historyRow.unit_price || 0)
  historyDialog.visible = false
  calculateTotal()
  save()
}

const addRow = () => {
  formData.items.push({ product_id: null, qty: 1, actual_price: 0 })
  save()
}

const removeRow = (index) => {
  formData.items.splice(index, 1)
  if (formData.items.length === 0) addRow()
  calculateTotal()
  save()
}

const calculateTotal = () => {
  formData.totalAmount = formData.items.reduce((sum, item) => sum + (item.qty || 0) * (item.actual_price || 0), 0)
  save()
}

const goPrev = () => {
  wizardStore.setCurrentStep(2)
  save()
  router.push('/sales/wizard/step2')
}

const goNext = () => {
  const validItems = formData.items.filter((item) => item.product_id)
  if (validItems.length === 0) return ElMessage.warning('请至少添加一行商品')

  const invalidPriceItem = validItems.find((i) => i.actual_price === undefined || i.actual_price === null || i.actual_price < 0)
  if (invalidPriceItem) return ElMessage.warning(`商品【${invalidPriceItem.product_name}】单价无效，请检查后重试`)

  if (wizardStore.orderType === 'retail') {
    const overSells = validItems.filter((i) => i.qty > (i.stock_quantity || 0))
    if (overSells.length > 0) {
      const names = overSells.map((i) => i.product_name).join('、')
      ElMessage.warning(`商品 ${names} 当前库存不足，请改为报价单`)
      return
    }
  }

  proceedToNext(validItems)
}

const proceedToNext = (validItems) => {
  wizardStore.items = validItems.map((item) => ({ ...item }))
  wizardStore.setCurrentStep(4)
  save()
  router.push('/sales/wizard/step4')
}

onMounted(async () => {
  if (!wizardStore.customerInfo) {
    ElMessage.warning('请先完成客户信息填写')
    router.push('/sales/wizard/step2')
    return
  }
  await catalog.searchProducts('')
  calculateTotal()
})
</script>

<style scoped>
.step-container { max-width: 1400px; margin: 0 auto; padding-top: 10px; }
.step-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.step-title { margin: 0; color: #303133; font-weight: 600; }
.items-table { margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05); }
.stock-warning { color: #f56c6c; font-weight: bold; }
.history-price { color: #409eff; font-weight: bold; }
.history-sub { font-size: 12px; color: #909399; }
.loading-text { color: #909399; font-size: 12px; }
.highlight-amount { color: #f56c6c; font-weight: bold; font-size: 15px; }
.price-cell { display: flex; flex-direction: column; line-height: 1.4; }

:deep(.el-table .duplicate-row-flash) {
  --el-table-tr-bg-color: #fdf6ec !important;
  transition: background-color 0.3s ease;
}

.summary-section {
  display: flex; justify-content: flex-end; padding: 16px 20px;
  background: #f8f9fa; border-radius: 8px 8px 0 0; border: 1px solid #ebeef5;
  margin-bottom: 0; border-bottom: none;
}
.summary-text { font-size: 16px; color: #606266; display: flex; align-items: baseline; }
.total-amount { font-size: 26px; color: #f56c6c; font-weight: bold; margin-left: 12px; }

.step-actions {
  display: flex; justify-content: space-between; padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid #ebeef5; border-top: none;
  border-radius: 0 0 8px 8px;
  position: sticky;
  bottom: 0;
  z-index: 100;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.05);
}
</style>
