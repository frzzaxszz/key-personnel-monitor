import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 20000 })

export const dashboardApi = {
  summary: (params = {}) => http.get('/dashboard/summary', { params }).then(r => r.data),
  map: (params = {}) => http.get('/dashboard/map', { params }).then(r => r.data)
}

export const personApi = {
  list: (params) => http.get('/persons', { params }).then(r => r.data),
  options: () => http.get('/persons/options').then(r => r.data),
  get: (id) => http.get(`/persons/${id}`).then(r => r.data),
  create: (data) => http.post('/persons', data).then(r => r.data),
  update: (id, data) => http.put(`/persons/${id}`, data).then(r => r.data),
  remove: (id) => http.delete(`/persons/${id}`).then(r => r.data),
  uploadPhoto: (id, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post(`/persons/${id}/photo`, fd).then(r => r.data)
  },
  visits: (id) => http.get(`/persons/${id}/visits`).then(r => r.data),
  addVisit: (id, data) => http.post(`/persons/${id}/visits`, data).then(r => r.data)
}

export const importApi = {
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/import/excel', fd).then(r => r.data)
  },
  logs: () => http.get('/import/logs').then(r => r.data)
}

export const settingsApi = {
  get: () => http.get('/settings/db').then(r => r.data),
  update: (data) => http.put('/settings/db', data).then(r => r.data),
  test: () => http.post('/settings/db/test').then(r => r.data),
  reseed: (count = 5000) => http.post('/settings/reseed', null, { params: { count } }).then(r => r.data),
  drop: () => http.post('/settings/drop').then(r => r.data)
}

export default http
