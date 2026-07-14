import { createI18n } from 'vue-i18n'
import en from './en.json'
import vi from './vi.json'

const savedLang = localStorage.getItem('dpg_asset_lang') || 'vi'

export const i18n = createI18n({
  legacy: false,
  locale: savedLang,
  fallbackLocale: 'en',
  messages: { en, vi },
})

export function setLocale(lang) {
  i18n.global.locale.value = lang
  localStorage.setItem('dpg_asset_lang', lang)
}
