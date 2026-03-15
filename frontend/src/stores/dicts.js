import { defineStore } from 'pinia'

export const useDictsStore = defineStore('dicts', {
  state: () => ({
    paymentMethods: [
      { label: '现金', value: 'cash' },
      { label: '微信', value: 'wechat' },
      { label: '支付宝', value: 'alipay' },
      { label: '银行转账', value: 'bank_transfer' },
      { label: '其他', value: 'other' },
    ],
    contactRoles: [
      { label: '维修工', value: '维修工' },
      { label: '老板', value: '老板' },
      { label: '会计', value: '会计' },
      { label: '采购', value: '采购' },
      { label: '拿货人', value: '拿货人' },
      { label: '本人', value: '本人' },
      { label: '其他', value: '其他' },
    ],
  }),
})