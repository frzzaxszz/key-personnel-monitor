import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/persons', name: 'persons', component: () => import('../views/PersonList.vue') },
  { path: '/persons/:id', name: 'person-detail', component: () => import('../views/PersonDetail.vue') },
  { path: '/import', name: 'import', component: () => import('../views/ImportData.vue') },
  { path: '/settings', name: 'settings', component: () => import('../views/Settings.vue') }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
