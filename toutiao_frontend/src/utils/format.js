export function formatDate(value, withSeconds = false) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'

  const pad = (number) => String(number).padStart(2, '0')
  const base = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
  return withSeconds ? `${base}:${pad(date.getSeconds())}` : base
}

export function formatViews(value) {
  const views = Number(value)
  return `${Number.isFinite(views) ? views : 0} 阅读`
}
