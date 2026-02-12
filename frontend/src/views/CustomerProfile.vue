<template>
  <div>
    <el-row :gutter="12" style="margin-bottom: 12px;">
      <el-col :span="12">
        <el-card>
          <template #header>客户信息</template>
          <div style="display:flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-size:16px; font-weight:700;">{{ customer?.name || '-' }}</div>
              <div style="margin-top:6px; color:#666;">电话：{{ customer?.phone || '-' }}</div>
              <div style="margin-top:6px; color:#666;">地址：{{ customer?.address || '-' }}</div>
            </div>
            <el-tag :type="customer?.is_active ? 'success' : 'info'">
              {{ customer?.is_active ? '启用' : '停用' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>欠款概览</template>
          <div style="display:flex; gap: 16px; flex-wrap: wrap;">
            <div>
              <div style="color:#666;">累计销售</div>
              <div style="font-size:18px; font-weight:700;">￥{{ arSummary.total_sales_amount?.toFixed(2) || '0.00' }}</div>
            </div>
            <div>
              <div style="color:#666;">累计已收</div>
              <div style="font-size:18px; font-weight:700;">￥{{ arSummary.total_paid_amount?.toFixed(2) || '0.00' }}</div>
            </div>
            <div>
              <div style="color:#666;">累计欠款</div>
              <div style="font-size:18px; font-weight:800; color:#d4380d;">
                ￥{{ arSummary.total_balance?.toFixed(2) || '0.00' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="对账/结算" name="statement">
          <div style="display:flex; justify-content: space-between; align-items:center; gap:12px; flex-wrap: wrap; margin-bottom: 12px;">
            <div style="display:flex; gap:10px; align-items:center; flex-wrap: wrap;">
              <span style="color:#666;">日期范围</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                unlink-panels
                range-separator="~"
                start-placeholder="开始"
                end-placeholder="结束"
                value-format=""
              />
              <el-button type="primary" @click="loadStatement()">查询</el-button>
              <el-button @click="resetRange()">本月</el-button>
            </div>

            <div style="display:flex; gap:10px; align-items:center;">
              <el-button type="success" :disabled="selectedSaleIds.length===0" @click="openBatchDialog()">
                批量收款
              </el-button>
            </div>
          </div>

          <el-alert
            :closable="false"
            type="info"
            show-icon
            style="margin-bottom: 12px;"
          >
            <template #default>
              <span style="margin-right: 14px;">应收：<b>￥{{ statement.summary.total_sales_amount.toFixed(2) }}</b></span>
              <span style="margin-right: 14px;">已收：<b>￥{{ statement.summary.total_paid_amount.toFixed(2) }}</b></span>
              <span>未收：<b style="color:#d4380d;">￥{{ statement.summary.total_balance.toFixed(2) }}</b></span>
            </template>
          </el-alert>

          <el-table
            :data="statement.items"
            border
            @selection-change="onSelectionChange"
            row-key="id"
          >
            <el-table-column type="selection" width="48" />
            <el-table-column prop="sale_date" label="日期" width="180">
              <template #default="{ row }">
                {{ formatDT(row.sale_date) }}
              </template>
            </el-table-column>

            <el-table-column prop="id" label="单号" width="100" />

            <el-table-column prop="project_name" label="项目" min-width="140" />
            <el-table-column prop="contact_name_snapshot" label="拿货人" width="120" />

            <el-table-column prop="total_amount" label="总额" width="120">
              <template #default="{ row }">￥{{ row.total_amount.toFixed(2) }}</template>
            </el-table-column>

            <el-table-column prop="paid_amount" label="已付" width="120">
              <template #default="{ row }">￥{{ row.paid_amount.toFixed(2) }}</template>
            </el-table-column>

            <el-table-column prop="balance" label="未付" width="120">
              <template #default="{ row }">
                <span :style="{ color: row.balance > 0 ? '#d4380d' : '#389e0d', fontWeight: 700 }">
                  ￥{{ row.balance.toFixed(2) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="payment_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.payment_status==='paid'" type="success">已付</el-tag>
                <el-tag v-else-if="row.payment_status==='partial'" type="warning">部分</el-tag>
                <el-tag v-else type="info">未付</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="note" label="备注" min-width="160" />

            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  :disabled="row.balance <= 0"
                  @click="openPayDialog(row)"
                >
                  收款
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div style="display:flex; justify-content:flex-end; margin-top:12px;">
            <el-pagination
              background
              layout="prev, pager, next, sizes, total"
              :total="statement.total"
              :page-size="statement.page_size"
              :current-page="statement.page"
              @current-change="(p)=>{statement.page=p; loadStatement()}"
              @size-change="(s)=>{statement.page_size=s; statement.page=1; loadStatement()}"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="联系人" name="contacts">
          <div style="display:flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="color:#666;">该客户下的维修工/会计/采购等联系人</div>
            <el-button type="primary" @click="openContactDialog()">新增联系人</el-button>
          </div>

          <el-table :data="contacts.items" border row-key="id">
            <el-table-column prop="name" label="姓名" width="140" />
            <el-table-column prop="role" label="角色" width="120" />
            <el-table-column prop="phone" label="电话" width="160" />
            <el-table-column prop="note" label="备注" min-width="200" />
            <el-table-column label="启用" width="100">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  @change="()=>toggleContact(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openContactDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div style="display:flex; justify-content:flex-end; margin-top:12px;">
            <el-pagination
              background
              layout="prev, pager, next, sizes, total"
              :total="contacts.total"
              :page-size="contacts.page_size"
              :current-page="contacts.page"
              @current-change="(p)=>{contacts.page=p; loadContacts()}"
              @size-change="(s)=>{contacts.page_size=s; contacts.page=1; loadContacts()}"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 单笔收款 Dialog -->
    <el-dialog v-model="payDialog.visible" title="收款" width="420px">
      <div style="margin-bottom: 10px; color:#666;">
        单据：#{{ payDialog.sale?.id }}，未付：<b style="color:#d4380d;">￥{{ (payDialog.sale?.balance || 0).toFixed(2) }}</b>
      </div>

      <el-form label-width="90px">
        <el-form-item label="金额">
          <el-input-number v-model="payDialog.form.amount" :min="0" :max="payDialog.sale?.balance || 0" :step="1" style="width: 100%;" />
        </el-form-item>

        <el-form-item label="方式">
          <el-select v-model="payDialog.form.method" style="width:100%;">
            <el-option v-for="m in dicts.paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker v-model="payDialog.form.paid_at" type="datetime" style="width:100%;" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="payDialog.form.note" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="payDialog.visible=false">取消</el-button>
        <el-button type="primary" :loading="payDialog.loading" @click="submitPayment()">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 批量收款 Dialog -->
    <el-dialog v-model="batchDialog.visible" title="批量收款（自动分配到多张单）" width="560px">
      <el-alert type="warning" show-icon :closable="false" style="margin-bottom: 10px;">
        <template #default>
          选中 {{ selectedSaleIds.length }} 张单，系统按“时间先后（FIFO）”自动分配收款。
        </template>
      </el-alert>

      <el-form label-width="110px">
        <el-form-item label="收款总额">
          <el-input-number v-model="batchDialog.form.total_amount" :min="0" :max="batchDialog.totalDue" :step="1" style="width: 100%;" />
          <div style="margin-top:6px; color:#666;">所选单据总欠款：￥{{ batchDialog.totalDue.toFixed(2) }}</div>
        </el-form-item>

        <el-form-item label="方式">
          <el-select v-model="batchDialog.form.method" style="width:100%;">
            <el-option v-for="m in dicts.paymentMethods" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间">
          <el-date-picker v-model="batchDialog.form.paid_at" type="datetime" style="width:100%;" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="batchDialog.form.note" placeholder="可选" />
        </el-form-item>
      </el-form>

      <div v-if="batchDialog.result.allocations.length" style="margin-top: 12px;">
        <div style="font-weight:700; margin-bottom:8px;">分配结果</div>
        <el-table :data="batchDialog.result.allocations" border size="small">
          <el-table-column prop="sale_id" label="单号" width="100" />
          <el-table-column prop="applied_amount" label="本次分配" width="120">
            <template #default="{ row }">￥{{ row.applied_amount.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="after_balance" label="分配后未付" width="140">
            <template #default="{ row }">￥{{ row.after_balance.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="after_status" label="状态" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="batchDialog.visible=false">关闭</el-button>
        <el-button type="primary" :loading="batchDialog.loading" @click="submitBatch()">执行批量收款</el-button>
      </template>
    </el-dialog>

    <!-- 联系人 Dialog -->
    <el-dialog v-model="contactDialog.visible" :title="contactDialog.editing ? '编辑联系人' : '新增联系人'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="姓名">
          <el-input v-model="contactDialog.form.name" placeholder="必填" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="contactDialog.form.role" style="width:100%;">
            <el-option v-for="r in dicts.contactRoles" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="contactDialog.form.phone" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="contactDialog.form.note" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="contactDialog.visible=false">取消</el-button>
        <el-button type="primary" :loading="contactDialog.loading" @click="submitContact()">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useDictsStore } from '../stores/dicts'
import { getCustomerStatement, getCustomerArSummary } from '../api/customers_ext'
import { listContacts, createContact, updateContact, toggleContact as apiToggleContact } from '../api/contacts'
import { createPayment, batchApplyPayments } from '../api/payments'

const route = useRoute()
const dicts = useDictsStore()

const customerId = Number(route.params.id)

const customer = ref(null) // 如果你已有 profile API，可在此加载客户详情；这里不强制
const arSummary = reactive({ total_sales_amount: 0, total_paid_amount: 0, total_balance: 0 })

const activeTab = ref('statement')

// 日期范围：默认本月
const dateRange = ref(null)
function setThisMonth() {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)
  dateRange.value = [start, end]
}
setThisMonth()

const statement = reactive({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  summary: { total_sales_amount: 0, total_paid_amount: 0, total_balance: 0 },
})

const selectedSaleIds = ref([])
function onSelectionChange(rows) {
  selectedSaleIds.value = rows.map((r) => r.id)
}

function formatDT(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

async function loadAr() {
  const data = await getCustomerArSummary(customerId)
  arSummary.total_sales_amount = data.total_sales_amount || 0
  arSummary.total_paid_amount = data.total_paid_amount || 0
  arSummary.total_balance = data.total_balance || 0
}

async function loadStatement() {
  const [start, end] = dateRange.value || []
  const params = {
    page: statement.page,
    page_size: statement.page_size,
    start_date: start ? start.toISOString() : undefined,
    end_date: end ? end.toISOString() : undefined,
  }
  const data = await getCustomerStatement(customerId, params)
  statement.items = data.items || []
  statement.total = data.total || 0
  statement.page = data.page || 1
  statement.page_size = data.page_size || 20
  statement.summary = data.summary || { total_sales_amount: 0, total_paid_amount: 0, total_balance: 0 }
}

function resetRange() {
  setThisMonth()
  statement.page = 1
  loadStatement()
}

function onTabChange() {
  if (activeTab.value === 'statement') loadStatement()
  if (activeTab.value === 'contacts') loadContacts()
}

const payDialog = reactive({
  visible: false,
  loading: false,
  sale: null,
  form: { amount: 0, method: '转账', paid_at: new Date(), note: '' },
})

function openPayDialog(row) {
  payDialog.sale = row
  payDialog.form.amount = row.balance
  payDialog.form.method = '转账'
  payDialog.form.paid_at = new Date()
  payDialog.form.note = ''
  payDialog.visible = true
}

async function submitPayment() {
  if (!payDialog.sale) return
  if (payDialog.form.amount <= 0) {
    ElMessage.warning('金额必须大于 0')
    return
  }
  payDialog.loading = true
  try {
    await createPayment({
      sale_id: payDialog.sale.id,
      amount: payDialog.form.amount,
      method: payDialog.form.method,
      paid_at: payDialog.form.paid_at ? payDialog.form.paid_at.toISOString() : undefined,
      note: payDialog.form.note || undefined,
    })
    ElMessage.success('收款已记录')
    payDialog.visible = false
    await loadStatement()
    await loadAr()
  } finally {
    payDialog.loading = false
  }
}

const batchDialog = reactive({
  visible: false,
  loading: false,
  totalDue: 0,
  form: { total_amount: 0, method: '转账', paid_at: new Date(), note: '' },
  result: { allocations: [] },
})

function openBatchDialog() {
  const selectedRows = statement.items.filter((r) => selectedSaleIds.value.includes(r.id))
  const due = selectedRows.reduce((sum, r) => sum + (r.balance || 0), 0)
  batchDialog.totalDue = Number(due.toFixed(2))
  batchDialog.form.total_amount = batchDialog.totalDue
  batchDialog.form.method = '转账'
  batchDialog.form.paid_at = new Date()
  batchDialog.form.note = ''
  batchDialog.result.allocations = []
  batchDialog.visible = true
}

async function submitBatch() {
  if (batchDialog.form.total_amount <= 0) {
    ElMessage.warning('收款总额必须大于 0')
    return
  }
  batchDialog.loading = true
  try {
    const data = await batchApplyPayments({
      customer_id: customerId,
      sale_ids: selectedSaleIds.value,
      total_amount: batchDialog.form.total_amount,
      method: batchDialog.form.method,
      paid_at: batchDialog.form.paid_at ? batchDialog.form.paid_at.toISOString() : undefined,
      note: batchDialog.form.note || undefined,
    })
    batchDialog.result.allocations = data.allocations || []
    ElMessage.success(`批量收款完成（生成 ${data.created_payments || 0} 条收款记录）`)
    await loadStatement()
    await loadAr()
  } finally {
    batchDialog.loading = false
  }
}

const contacts = reactive({ items: [], total: 0, page: 1, page_size: 20 })

async function loadContacts() {
  const data = await listContacts(customerId, { page: contacts.page, page_size: contacts.page_size })
  contacts.items = data.items || []
  contacts.total = data.total || 0
  contacts.page = data.page || 1
  contacts.page_size = data.page_size || 20
}

async function toggleContact(row) {
  // row.is_active 已先被切换，接口返回后再覆盖
  const updated = await apiToggleContact(row.id)
  row.is_active = updated.is_active
  ElMessage.success('状态已更新')
}

const contactDialog = reactive({
  visible: false,
  loading: false,
  editing: false,
  contactId: null,
  form: { name: '', role: '维修工', phone: '', note: '' },
})

function openContactDialog(row = null) {
  contactDialog.editing = !!row
  contactDialog.contactId = row?.id || null
  contactDialog.form.name = row?.name || ''
  contactDialog.form.role = row?.role || '维修工'
  contactDialog.form.phone = row?.phone || ''
  contactDialog.form.note = row?.note || ''
  contactDialog.visible = true
}

async function submitContact() {
  if (!contactDialog.form.name?.trim()) {
    ElMessage.warning('姓名必填')
    return
  }
  contactDialog.loading = true
  try {
    if (contactDialog.editing) {
      await updateContact(contactDialog.contactId, {
        name: contactDialog.form.name,
        role: contactDialog.form.role,
        phone: contactDialog.form.phone || null,
        note: contactDialog.form.note || null,
      })
      ElMessage.success('联系人已更新')
    } else {
      await createContact(customerId, {
        name: contactDialog.form.name,
        role: contactDialog.form.role,
        phone: contactDialog.form.phone || null,
        note: contactDialog.form.note || null,
      })
      ElMessage.success('联系人已新增')
    }
    contactDialog.visible = false
    await loadContacts()
  } finally {
    contactDialog.loading = false
  }
}

onMounted(async () => {
  // customer 信息如果你已有 /customers/{id}/profile，可在此加载并赋值 customer.value
  await loadAr()
  await loadStatement()
})
</script>
