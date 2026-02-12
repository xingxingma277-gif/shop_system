import { defineStore } from 'pinia'

export const useDictsStore = defineStore('dicts', {
  state: () => ({
    paymentMethods: [
      { label: '现金', value: '现金' },
      { label: '微信', value: '微信' },
      { label: '支付宝', value: '支付宝' },
      { label: '转账', value: '转账' },
      { label: '其他', value: '其他' },
    ],
    contactRoles: [
      { label: '维修工', value: '维修工' },
      { label: '老板', value: '老板' },
      { label: '会计', value: '会计' },
      { label: '采购', value: '采购' },
      { label: '其他', value: '其他' },
    ],
  }),
})
