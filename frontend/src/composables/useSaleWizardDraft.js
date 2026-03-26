import { watch } from 'vue'

export function useSaleWizardDraft(wizardStore) {
  const save = () => wizardStore.saveDraftToLocal()

  const bindAutoSave = (source, options = { deep: true }) => {
    return watch(source, () => {
      save()
    }, options)
  }

  return {
    save,
    bindAutoSave
  }
}
