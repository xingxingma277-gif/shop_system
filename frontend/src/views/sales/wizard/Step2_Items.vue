<template>
  <div class="step-container">
    <h3 class="step-title">第二步：选择客户</h3>

    <el-form label-width="120px" class="step-form">
      <el-form-item label="选择客户" required>
        <div style="display: flex; gap: 10px; width: 100%;">
          <el-select
            v-model="formData.customer_id"
            filterable
            remote
            :remote-method="onSearchCustomers"
            placeholder="请输入拼音或名称搜索"
            style="flex: 1;"
            @change="handleCustomerChange"
          >
            <el-option v-for="c in catalog.customers" :key="c.id" :label="c.name" :value="c.id">
              <span style="float: left">{{ c.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ c.type === 'company' ? '🏢 公司' : '👤 个人' }}
              </span>
            </el-option>
          </el-select>
          <el-button type="success" plain @click="goToCustomerPage">+ 新建客户</el-button>
        </div>
      </el-form-item>

      <el-form-item label="拿货人" v-if="selectedCustomerType === 'company'">
        <div style="display: flex; gap: 10px; width: 100%;">
          <el-select
            v-model="formData.buyerId"
            placeholder="请选择拿货人（可选）"
            style="flex: 1;"
            clearable
            @change="handleBuyerChange"
          >
            <el-option v-for="b in buyerOptions" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
          <el-button type="primary" plain @click="showBuyerDialog = true">+ 新增拿货人</el-button>
        </div>
      </el-form-item>

      <el-form-item label="项目">
        <el-input v-model="formData.project" placeholder="请输入项目名称（可选）" />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          type="textarea"
          v-model="formData.remark"
          placeholder="请输入发货要求或其他备注信息（可选）"
          :rows="3"
        />
      </el-form-item>

      <div class="step-actions">
        <el-button size="large" @click="goPrev">返回单据类型</el-button>
        <el-button type="primary" size="large" @click="goNext">下一步：添加商品</el-button>
      </div>
    </el-form>

    <el-dialog v-model="showBuyerDialog" title="新增拿货人" width="400px">
      <el-form label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="newBuyer.name" placeholder="请输入拿货人姓名" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="newBuyer.phone" placeholder="请输入手机号（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBuyerDialog = false">取消</el-button>
        <el-button type="primary" @click="submitNewBuyer" :loading="isSavingBuyer">保存并选中</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useSaleWizardStore } from '../../../stores/saleWizard'
import { useCatalogStore } from '../../../stores/catalog'
import { useSaleWizardDraft } from '../../../composables/useSaleWizardDraft'
import { createBuyer, listBuyers } from '../../../api/customers'

const router = useRouter()
const wizardStore = useSaleWizardStore()
const catalog = useCatalogStore()
const { save } = useSaleWizardDraft(wizardStore)

const selectedCustomerType = ref('')
const buyerOptions = ref([])

const formData = reactive({
  customer_id: wizardStore.customerInfo?.id || null,
  buyerId: wizardStore.buyerId || null,
  project: wizardStore.project || '',
  remark: wizardStore.remark || ''
})

const showBuyerDialog = ref(false)
const isSavingBuyer = ref(false)
const newBuyer = reactive({ name: '', phone: '' })

watch(
  () => [formData.customer_id, formData.buyerId, formData.project, formData.remark],
  () => {
    const customer = catalog.customers.find((c) => c.id === formData.customer_id) || null
    wizardStore.customerInfo = customer
    wizardStore.buyerId = formData.buyerId
    wizardStore.buyerName = buyerOptions.value.find((b) => b.id === formData.buyerId)?.name || ''
    wizardStore.project = formData.project
    wizardStore.remark = formData.remark
    wizardStore.setCurrentStep(2)
    save()
  },
  { deep: true }
)

const onSearchCustomers = async (q) => {
  await catalog.searchCustomers(q || '')
}

const loadBuyerOptions = async (customerId) => {
  try {
    buyerOptions.value = await listBuyers(customerId)
  } catch (error) {
    buyerOptions.value = []
  }
}

const handleCustomerChange = async (customerId) => {
  formData.buyerId = null
  wizardStore.buyerName = ''
  const customer = catalog.customers.find((c) => c.id === customerId)
  if (!customer) return

  selectedCustomerType.value = customer.type || 'company'
  if (selectedCustomerType.value === 'company') {
    await loadBuyerOptions(customerId)
  } else {
    buyerOptions.value = []
  }
}

const handleBuyerChange = (buyerId) => {
  wizardStore.buyerName = buyerOptions.value.find((b) => b.id === buyerId)?.name || ''
  save()
}

const goToCustomerPage = () => {
  save()
  router.push({ path: '/customers', query: { from: 'sale_wizard', action: 'create' } })
}

const submitNewBuyer = async () => {
  if (!newBuyer.name) return ElMessage.warning('姓名不能为空')
  isSavingBuyer.value = true
  try {
    const createdBuyer = await createBuyer(formData.customer_id, {
      name: newBuyer.name,
      phone: newBuyer.phone || '未提供',
      customer_id: formData.customer_id
    })

    buyerOptions.value.push(createdBuyer)
    formData.buyerId = createdBuyer.id
    wizardStore.buyerName = createdBuyer.name

    ElMessage.success('拿货人新增成功，已同步至客户档案')
    showBuyerDialog.value = false
    newBuyer.name = ''
    newBuyer.phone = ''
    save()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '添加拿货人失败')
  } finally {
    isSavingBuyer.value = false
  }
}

const goPrev = () => {
  wizardStore.setCurrentStep(1)
  save()
  router.push('/sales/wizard/step1')
}

const goNext = () => {
  if (!formData.customer_id) {
    ElMessage.warning('请先选择客户')
    return
  }

  wizardStore.setCurrentStep(3)
  save()
  router.push('/sales/wizard/step3')
}

onMounted(async () => {
  await catalog.searchCustomers('')
  if (formData.customer_id) {
    await handleCustomerChange(formData.customer_id)
  }
})
</script>

<style scoped>
.step-container { max-width: 600px; margin: 0 auto; padding-top: 40px; }
.step-title { text-align: center; margin-bottom: 40px; color: #303133; font-weight: 600; }
.step-form { background: #f8f9fa; padding: 40px 30px; border-radius: 8px; border: 1px solid #e4e7ed; }
.step-actions { display: flex; justify-content: space-between; border-top: 1px solid #ebeef5; padding-top: 20px; margin-top: 20px; }
</style>
