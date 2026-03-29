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
  sourceQuoteId: null,
  editingQuoteId: null,
  quoteUpdatedAt: null,
  isSubmitted: false,
  updatedAt: null
})

const cloneState = (state) => ({
  ...state,
  items: Array.isArray(state.items) ? state.items.map((item) => ({ ...item })) : [],
  settlement: { ...(state.settlement || {}) }
})

export const useSaleWizardStore = defineStore('saleWizard', {
  state: () => getDefaultState(),
  actions: {
    saveDraftToLocal() {
      this.updatedAt = new Date().toISOString()
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(cloneState(this.$state)))
    },

    loadDraftFromLocal() {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (!raw) return false
      try {
        const parsed = JSON.parse(raw)
        this.$patch({
          ...getDefaultState(),
          ...parsed,
          settlement: {
            ...getDefaultState().settlement,
            ...(parsed?.settlement || {})
          },
          items: Array.isArray(parsed?.items) ? parsed.items : []
        })
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
      if (this.orderType !== 'retail') return true
      if (this.customerInfo?.id) return true
      if (this.buyerId) return true
      if ((this.project || '').trim()) return true
      if ((this.remark || '').trim()) return true
      if (this.sourceQuoteId) return true
      if (this.editingQuoteId) return true
      if (this.items.some((item) => item?.product_id || item?.qty || item?.actual_price)) return true
      return false
    },

    markSubmitted() {
      this.isSubmitted = true
      this.updatedAt = new Date().toISOString()
    },

    setCurrentStep(step) {
      const num = Number(step)
      this.currentStep = Number.isFinite(num) ? Math.min(5, Math.max(1, num)) : 1
    }
  }
})
