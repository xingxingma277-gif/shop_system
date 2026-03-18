import { createRouter, createWebHistory } from 'vue-router'

import NewSale from '../views/NewSale.vue'
import Products from '../views/Products.vue'
import Customers from '../views/Customers.vue'
import CustomerProfile from '../views/CustomerProfile.vue'
import SaleCheckout from '../views/SaleCheckout.vue'
import SaleDetail from '../views/SaleDetail.vue'
import Transactions from '../views/Transactions.vue'
import InventoryLedger from '../views/InventoryLedger.vue'
import AccountsPayable from '../views/AccountsPayable.vue'
import Purchases from '../views/Purchases.vue'
import Warehouses from '../views/Warehouses.vue'
import Suppliers from '../views/Suppliers.vue'
import Reports from '../views/Reports.vue'
import InventoryAdjustments from '../views/InventoryAdjustments.vue'

const routes = [
  { path: '/', redirect: '/new-sale' },
  { path: '/new-sale', component: NewSale, meta: { title: '开单' } },
  { path: '/products', component: Products, meta: { title: '商品管理' } },
  { path: '/customers', component: Customers, meta: { title: '客户管理' } },
  { path: '/customers/:id', component: CustomerProfile, meta: { title: '客户档案' } },
  { path: '/transactions', component: Transactions, meta: { title: '交易记录' } },
  { path: '/suppliers', component: Suppliers, meta: { title: '供应商管理' } },
  { path: '/warehouses', component: Warehouses, meta: { title: '仓库管理' } },
  { path: '/purchases', component: Purchases, meta: { title: '采购管理' } },
  { path: '/inventory-ledger', component: InventoryLedger, meta: { title: '库存台账' } },
  { path: '/inventory-adjustments', component: InventoryAdjustments, meta: { title: '库存调整' } },
  { path: '/accounts-payable', component: AccountsPayable, meta: { title: '应付管理' } },
  { path: '/reports', component: Reports, meta: { title: '经营报表' } },
  { path: '/sales/:id', component: SaleDetail, meta: { title: '订单详情' } },
  { path: '/sales/:id/payment', component: SaleCheckout, meta: { title: '收款' } },
  { path: '/sales/:id/checkout', redirect: (to) => `/sales/${to.params.id}/payment` },
  { path: '/checkout', component: SaleCheckout, meta: { title: '收款' } }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
