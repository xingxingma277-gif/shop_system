import { defineStore } from 'pinia'
import { listCustomers } from '../api/customers'
import { listProducts } from '../api/products'

export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    customers: [],
    products: []
  }),
  actions: {
    async searchCustomers(q) {
      const res = await listCustomers({ page: 1, page_size: 20, q, active_only: false })
      this.customers = res.items
      return this.customers
    },
    async searchProducts(q) {
      const res = await listProducts({ page: 1, page_size: 20, q, active_only: false })
      this.products = res.items
      return this.products
    }
  }
})
