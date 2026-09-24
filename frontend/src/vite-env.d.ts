/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_USE_MOCKS?: string
  readonly VITE_API_MODE?: 'legacy' | 'v1'
  readonly VITE_PRIVACY_EMAIL?: string
}
interface ImportMeta { readonly env: ImportMetaEnv }
