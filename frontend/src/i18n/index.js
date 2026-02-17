import { createI18n } from 'vue-i18n'
import ru from './ru.js'
import uz from './uz.js'

const savedLocale = localStorage.getItem('locale') || 'ru'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'ru',
  messages: { ru, uz },
})

export default i18n
