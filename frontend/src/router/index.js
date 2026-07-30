import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/pages/Login.vue') },
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/Home.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets',
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
    path: '/requests/new/:type',
    name: 'request-new',
    component: () => import('@/pages/requests/RequestForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/archive',
    name: 'requests-archive',
    component: () => import('@/pages/RequestsArchive.vue'),
    meta: { requiresAuth: true, requiresAssetManager: true },
  },
  {
    path: '/requests/:id',
    name: 'request-detail',
    component: () => import('@/pages/requests/RequestDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/pages/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/companies',
    name: 'admin-companies',
    component: () => import('@/pages/admin/Companies.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('@/pages/admin/Users.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/council-members',
    name: 'admin-council-members',
    component: () => import('@/pages/admin/CouncilMembers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
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
  if (to.meta.requiresAdmin && !auth.isAdmin) return '/'
  if (to.meta.requiresAssetManager && !auth.isAssetManager) return '/'
  if (to.path === '/login' && auth.isAuthenticated) return '/'
})

export default router
