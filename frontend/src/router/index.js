import { createRouter, createWebHistory } from 'vue-router'

import NewSale from '../views/NewSale.vue'
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
import PurchaseDetail from '../views/PurchaseDetail.vue'
import Warehouses from '../views/Warehouses.vue'
import Suppliers from '../views/Suppliers.vue'
import Reports from '../views/Reports.vue'
import InventoryAdjustments from '../views/InventoryAdjustments.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AuditLogs from '../views/AuditLogs.vue'
import Login from '../views/Login.vue'

const routes = [
  { path: '/', redirect: '/new-sale' },
  { path: '/login', component: Login, meta: { title: '登录' } },
  { path: '/new-sale', component: NewSale, meta: { title: '开单' } },
  { path: '/products', component: Products, meta: { title: '商品管理' } },
  { path: '/customers', component: Customers, meta: { title: '客户管理' } },
  { path: '/customers/:id', component: CustomerProfile, meta: { title: '客户档案' } },
  { path: '/transactions', component: Transactions, meta: { title: '交易记录' } },
  { path: '/suppliers', component: Suppliers, meta: { title: '供应商管理' } },
  { path: '/warehouses', component: Warehouses, meta: { title: '仓库管理' } },
  { path: '/purchases', component: Purchases, meta: { title: '采购管理' } },
  { path: '/purchases/:id', component: PurchaseDetail, meta: { title: '采购单详情' } },
  { path: '/inventory-ledger', component: InventoryLedger, meta: { title: '库存台账' } },
  { path: '/inventory-checks', component: InventoryChecks, meta: { title: '库存盘点' } },
  { path: '/inventory-transfers', component: InventoryTransfers, meta: { title: '库存调拨' } },
  { path: '/inventory-adjustments', component: InventoryAdjustments, meta: { title: '库存调整' } },
  { path: '/accounts-payable', component: AccountsPayable, meta: { title: '应付管理' } },
  { path: '/reports', component: Reports, meta: { title: '经营报表' } },
  { path: '/admin/users', component: AdminUsers, meta: { title: '用户与角色' } },
  { path: '/admin/audit-logs', component: AuditLogs, meta: { title: '操作审计' } },
  { path: '/sales/:id', component: SaleDetail, meta: { title: '订单详情' } },
  { path: '/sales/:id/payment', component: SaleCheckout, meta: { title: '收款' } },
  { path: '/sales/:id/checkout', redirect: (to) => `/sales/${to.params.id}/payment` },
  { path: '/checkout', component: SaleCheckout, meta: { title: '收款' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  if (!to.path.startsWith('/admin')) return true
  const username = localStorage.getItem('shop:auth_user')
  if (username) return true
  return { path: '/login', query: { redirect: to.fullPath } }
})

export default router
