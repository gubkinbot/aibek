import { useI18n } from 'vue-i18n'

export function useDateFormat() {
  const { t, tm, locale } = useI18n()

  function formatDate(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const day = d.getDate()
    const month = tm('monthsShort')[d.getMonth()]
    const year = d.getFullYear()
    return `${day} ${month} ${year}`
  }

  function formatDateLong(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const day = d.getDate()
    const month = tm('months')[d.getMonth()]
    const year = d.getFullYear()
    return `${day} ${month} ${year}`
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const day = d.getDate()
    const month = tm('monthsShort')[d.getMonth()]
    const year = d.getFullYear()
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    return `${day} ${month} ${year}, ${hours}:${minutes}`
  }

  return { formatDate, formatDateLong, formatDateTime }
}
