// 按 key 防抖（适合表格每一行独立防抖）
export function debounceByKey(fn, wait = 300) {
  const timers = new Map()
  return (key, ...args) => new Promise((resolve, reject) => {
    if (timers.has(key)) clearTimeout(timers.get(key))
    const t = setTimeout(async () => {
      timers.delete(key)
      try {
        const res = await fn(...args)
        resolve(res)
      } catch (e) {
        reject(e)
      }
    }, wait)
    timers.set(key, t)
  })
}
