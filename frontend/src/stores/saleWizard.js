import { defineStore } from 'pinia'

const DRAFT_STORAGE_KEY = 'shop:sale_wizard:draft'

const getDefaultState = () => ({
  currentStep: 1,
  orderType: 'retail',
  customerInfo: null,
  buyerId: null,
  buyerName: '',
  project: '',
  remark: '',
  items: [],
  totalAmount: 0,
  settlement: {
    settlement_status: 'PAID',
    paid_amount: 0,
    payment_method: 'bank_transfer',
    payment_note: ''
  },
  updatedAt: null,
  isSubmitted: false
})

const shallowCopyState = (state) => ({
  ...state,
  settlement: { ...state.settlement },
  items: Array.isArray(state.items) ? state.items.map((item) => ({ ...item })) : []
})

export const useSaleWizardStore = defineStore('saleWizard', {
  state: () => getDefaultState(),
  actions: {
    saveDraftToLocal() {
      this.updatedAt = new Date().toISOString()
      const snapshot = {
        ...shallowCopyState(this.$state),
        updatedAt: this.updatedAt
      }
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(snapshot))
    },

    loadDraftFromLocal() {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (!raw) return false
      try {
        const parsed = JSON.parse(raw)
        const merged = {
          ...getDefaultState(),
          ...parsed,
          settlement: {
            ...getDefaultState().settlement,
            ...(parsed?.settlement || {})
          },
          items: Array.isArray(parsed?.items) ? parsed.items : []
        }
        this.$patch(merged)
        return true
      } catch (error) {
        localStorage.removeItem(DRAFT_STORAGE_KEY)
        return false
      }
    },

    clearDraft() {
      this.$patch(getDefaultState())
      localStorage.removeItem(DRAFT_STORAGE_KEY)
    },

    hasMeaningfulDraft() {
      if (this.isSubmitted) return false
      if (this.customerInfo?.id) return true
      if (this.buyerId) return true
      if ((this.project || '').trim()) return true
      if ((this.remark || '').trim()) return true
      if (Array.isArray(this.items) && this.items.some((item) => item?.product_id || item?.qty || item?.actual_price)) return true
      return this.orderType !== 'retail'
    },

    markSubmitted() {
      this.isSubmitted = true
      this.updatedAt = new Date().toISOString()
    },

    setCurrentStep(step) {
      const value = Number(step)
      this.currentStep = Number.isFinite(value) ? Math.min(4, Math.max(1, value)) : 1
    }
  }
})
