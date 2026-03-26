import { defineStore } from 'pinia'

export const useSaleWizardStore = defineStore('saleWizard', {
  state: () => ({
    // 第1步数据
    orderType: 'retail',

    // 第2步数据
    customerInfo: null,
    buyerId: null,               // 拿货人 ID
    projectRemarks: '',          // 合并后的 项目/备注 字段

    // 第3步数据
    items: [],
    totalAmount: 0
  }),
  actions: {
    clearDraft() {
      this.orderType = 'retail'
      this.customerInfo = null
      this.buyerId = null
      this.projectRemarks = ''
      this.items = []
      this.totalAmount = 0
    }
  }
})