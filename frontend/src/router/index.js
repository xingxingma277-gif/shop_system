import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '../layouts/MainLayout.vue'

import Dashboard from '../views/Dashboard.vue'
import Products from '../views/Products.vue'
import Customers from '../views/Customers.vue'
import CustomerProfile from '../views/CustomerProfile.vue'
import SaleCheckout from '../views/SaleCheckout.vue'
import SaleDetail from '../views/SaleDetail.vue'
import Transactions from '../views/Transactions.vue'
import InventoryLedger from '../views/InventoryLedger.vue'
import InventoryChecks from '../views/InventoryChecks.vue'
import InventoryTransfers from '../views/InventoryTransfers.vue'
import AccountsPayable from '../views/AccountsPayable.vue'
import Purchases from '../views/Purchases.vue'
import PurchaseCreate from '../views/PurchaseCreate.vue'
import PurchaseDetail from '../views/PurchaseDetail.vue'
import Warehouses from '../views/Warehouses.vue'
import Suppliers from '../views/Suppliers.vue'
import Reports from '../views/Reports.vue'
import InventoryAdjustments from '../views/InventoryAdjustments.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AuditLogs from '../views/AuditLogs.vue'
import Login from '../views/Login.vue'
import { getAuthToken, getStoredAuth, hasPermission } from '../utils/auth'

const routes = [
  { path: '/login', component: Login, meta: { title: '登录' } },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Dashboard, meta: { title: '经营看板', requiresAuth: true, permission: 'report.view' } },

      { path: 'new-sale', redirect: '/sales/wizard/step1' },

      {
        path: 'sales/wizard',
        component: () => import('../views/sales/wizard/Layout.vue'),
        redirect: '/sales/wizard/step1',
        children: [
          { path: 'step1', component: () => import('../views/sales/wizard/Step1_Customer.vue'), meta: { title: '选择客户', requiresAuth: true, permission: 'sale.manage' } },
          { path: 'step2', component: () => import('../views/sales/wizard/Step2_Items.vue'), meta: { title: '添加商品', requiresAuth: true, permission: 'sale.manage' } },
          { path: 'step3', component: () => import('../views/sales/wizard/Step3_Verify.vue'), meta: { title: '价格与金额', requiresAuth: true, permission: 'sale.manage' } },
          { path: 'step4', component: () => import('../views/sales/wizard/Step4_Checkout.vue'), meta: { title: '结算与提交', requiresAuth: true, permission: 'sale.manage' } }
        ]
      },

      { path: 'products', component: Products, meta: { title: '商品管理', requiresAuth: true, permission: 'product.manage' } },
      { path: 'customers', component: Customers, meta: { title: '客户管理', requiresAuth: true, permission: 'customer.manage' } },
      { path: 'customers/:id', component: CustomerProfile, meta: { title: '客户档案', requiresAuth: true, permission: 'customer.view' } },
      { path: 'transactions', component: Transactions, meta: { title: '交易记录', requiresAuth: true, permission: 'transaction.view' } },
      { path: 'suppliers', component: Suppliers, meta: { title: '供应商管理', requiresAuth: true, permission: 'purchase.manage' } },
      { path: 'warehouses', component: Warehouses, meta: { title: '仓库管理', requiresAuth: true, permission: 'inventory.manage' } },

      { path: 'purchases', component: Purchases, meta: { title: '采购单据', requiresAuth: true, permission: 'purchase.manage' } },
      { path: 'purchases/new', component: PurchaseCreate, meta: { title: '新建采购单', requiresAuth: true, permission: 'purchase.manage' } },
      { path: 'purchases/:id', component: PurchaseDetail, meta: { title: '采购单详情', requiresAuth: true, permission: 'purchase.view' } },

      { path: 'inventory-ledger', component: InventoryLedger, meta: { title: '库存台账', requiresAuth: true, permission: 'inventory.view' } },
      { path: 'inventory-checks', component: InventoryChecks, meta: { title: '库存盘点', requiresAuth: true, permission: 'inventory.manage' } },
      { path: 'inventory-transfers', component: InventoryTransfers, meta: { title: '库存调拨', requiresAuth: true, permission: 'inventory.manage' } },
      { path: 'inventory-adjustments', component: InventoryAdjustments, meta: { title: '库存调整', requiresAuth: true, permission: 'inventory.manage' } },
      { path: 'accounts-payable', component: AccountsPayable, meta: { title: '应付管理', requiresAuth: true, permission: 'purchase.manage' } },
      { path: 'reports', component: Reports, meta: { title: '经营报表', requiresAuth: true, permission: 'report.view' } },
      { path: 'admin/users', component: AdminUsers, meta: { title: '用户与角色', requiresAuth: true, permission: 'admin.user.manage' } },
      { path: 'admin/audit-logs', component: AuditLogs, meta: { title: '操作审计', requiresAuth: true, permission: 'audit.view' } },
      { path: 'sales/:id', component: SaleDetail, meta: { title: '订单详情', requiresAuth: true, permission: 'sale.view' } },
      { path: 'sales/:id/payment', component: SaleCheckout, meta: { title: '收款', requiresAuth: true, permission: 'sale.manage' } },
      { path: 'checkout', component: SaleCheckout, meta: { title: '收款', requiresAuth: true, permission: 'sale.manage' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (!to.meta?.requiresAuth) return true
  const token = getAuthToken()
  if (!token) return { path: '/login', query: { redirect: to.fullPath } }
  const requiredPermission = to.meta?.permission
  const auth = getStoredAuth()
  if (!requiredPermission || hasPermission(requiredPermission)) return true
  if (!auth) return { path: '/login', query: { redirect: to.fullPath } }
  return { path: '/dashboard' }
})

export default router