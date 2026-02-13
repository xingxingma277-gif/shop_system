import { createRouter, createWebHistory } from 'vue-router'

import NewSale from '../views/NewSale.vue'
import Products from '../views/Products.vue'
import Customers from '../views/Customers.vue'
import CustomerProfile from '../views/CustomerProfile.vue'
import SaleCheckout from '../views/SaleCheckout.vue'

const routes = [
  { path: '/', redirect: '/new-sale' },
  { path: '/new-sale', component: NewSale, meta: { title: '开单' } },
  { path: '/products', component: Products, meta: { title: '商品管理' } },
  { path: '/customers', component: Customers, meta: { title: '客户管理' } },
  { path: '/customers/:id', component: CustomerProfile, meta: { title: '客户档案' } },
  { path: '/sales/:id/checkout', component: SaleCheckout, meta: { title: '收款确认' } },
  { path: '/checkout', component: SaleCheckout, meta: { title: '收款确认' } }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
