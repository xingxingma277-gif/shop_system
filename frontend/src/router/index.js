import { createRouter, createWebHistory } from 'vue-router'

import NewSale from '../views/NewSale.vue'
import Products from '../views/Products.vue'
import Customers from '../views/Customers.vue'
import CustomerProfile from '../views/CustomerProfile.vue'
import SaleCheckout from '../views/SaleCheckout.vue'
import SaleDetail from '../views/SaleDetail.vue'
import Transactions from '../views/Transactions.vue'

const routes = [
  { path: '/', redirect: '/new-sale' },
  { path: '/new-sale', component: NewSale, meta: { title: '开单' } },
  { path: '/products', component: Products, meta: { title: '商品管理' } },
  { path: '/customers', component: Customers, meta: { title: '客户管理' } },
  { path: '/customers/:id', component: CustomerProfile, meta: { title: '客户档案' } },
  { path: '/transactions', component: Transactions, meta: { title: '交易记录' } },
  { path: '/sales/:id', component: SaleDetail, meta: { title: '订单详情' } },
  { path: '/sales/:id/checkout', component: SaleCheckout, meta: { title: '收款确认' } },
  { path: '/checkout', component: SaleCheckout, meta: { title: '收款确认' } }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
