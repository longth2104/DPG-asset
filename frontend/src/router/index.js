import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/pages/Login.vue') },
  {
    path: '/',
    name: 'assets',
    component: () => import('@/pages/Assets.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets/new',
    name: 'asset-new',
    component: () => import('@/pages/CreateAsset.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets/:id',
    name: 'asset-detail',
    component: () => import('@/pages/AssetDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/pages/Profile.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.ensureInit()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/'
})

export default router
