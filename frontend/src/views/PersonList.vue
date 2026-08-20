<template>
  <div class="admin-page">
    <div class="page-head">
      <h2>重点人员管理</h2>
      <div class="head-actions">
        <router-link to="/dashboard" class="btn">← 返回大屏</router-link>
        <a class="btn" :href="`${baseURL}/api/import/export`">导出 Excel</a>
        <button class="btn btn-primary" @click="openCreate">+ 新增人员</button>
      </div>
    </div>
    <div class="admin-card">
      <div class="admin-toolbar">
        <input v-model="filters.q" class="input" placeholder="姓名 / 身份证 / 手机号" @keyup.enter="load(1)" style="width: 220px" />
        <select v-model="filters.category" class="select" @change="load(1)"><option value="">全部类别</option><option v-for="c in options.categories" :key="c" :value="c">{{ c }}</option></select>
        <select v-model="filters.risk_level" class="select" @change="load(1)"><option value="">全部风险</option><option v-for="r in options.risk_levels" :key="r" :value="r">{{ r }}</option></select>
        <select v-model="filters.control_status" class="select" @change="load(1)"><option value="">全部状态</option><option v-for="s in options.control_statuses" :key="s" :value="s">{{ s }}</option></select>
        <select v-model="filters.district" class="select" @change="load(1)"><option value="">全部地区</option><option v-for="d in options.districts" :key="d" :value="d">{{ d }}</option></select>
        <button class="btn" @click="load(1)">查询</button>
        <button class="btn" @click="resetFilters">重置</button>
      </div>
      <table class="grid-table">
        <thead><tr><th>照片</th><th>姓名</th><th>身份证号</th><th>类别</th><th>风险</th><th>状态</th><th>地区</th><th>责任民警</th><th>更新时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="p in list" :key="p.id">
            <td><img v-if="p.photo" :src="p.photo" class="avatar" /><span v-else class="avatar avatar-empty">{{ p.name[0] }}</span></td>
            <td><router-link class="text-link" :to="`/persons/${p.id}`">{{ p.name }}</router-link></td>
            <td>{{ p.id_card }}</td><td>{{ p.category }}</td>
            <td><span class="tag" :class="riskClass(p.risk_level)">{{ p.risk_level }}</span></td>
            <td><span class="tag" :class="statusClass(p.control_status)">{{ p.control_status }}</span></td>
            <td>{{ p.district }}</td><td>{{ p.manager }}</td><td>{{ fmtTime(p.updated_at) }}</td>
            <td><span class="text-link" style="margin-right: 10px" @click="openEdit(p)">编辑</span><span class="text-link" style="color: var(--accent-red)" @click="remove(p)">删除</span></td>
          </tr>
          <tr v-if="!list.length"><td colspan="10" class="empty">暂无数据</td></tr>
        </tbody>
      </table>
      <div class="pagination">
        <button class="page-btn" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
        <span class="text-muted">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
        <button class="page-btn" :disabled="page >= totalPages" @click="load(page + 1)">下一页</button>
      </div>
    </div>
    <div class="modal-mask" v-if="showForm">
      <div class="modal">
        <div class="modal-head"><span>{{ form.id ? '编辑人员' : '新增人员' }}</span><button class="modal-close" @click="showForm = false">×</button></div>
        <div class="modal-body">
          <div class="photo-box"><img v-if="photoPreview" :src="photoPreview" class="photo-preview" /><div v-else class="photo-preview empty">无照片</div><input type="file" accept="image/*" @change="onPhotoChange" class="input" style="width: 100%" /></div>
          <div class="form-grid">
            <label>姓名 *<input v-model="form.name" class="input" /></label>
            <label>身份证号 *<input v-model="form.id_card" class="input" /></label>
            <label>性别<select v-model="form.gender" class="select"><option>男</option><option>女</option></select></label>
            <label>年龄<input v-model.number="form.age" type="number" class="input" /></label>
            <label>手机号<input v-model="form.phone" class="input" /></label>
            <label>人员类别<select v-model="form.category" class="select"><option v-for="c in options.categories" :key="c" :value="c">{{ c }}</option></select></label>
            <label>风险等级<select v-model="form.risk_level" class="select"><option v-for="r in options.risk_levels" :key="r" :value="r">{{ r }}</option></select></label>
            <label>管控状态<select v-model="form.control_status" class="select"><option v-for="s in options.control_statuses" :key="s" :value="s">{{ s }}</option></select></label>
            <label>所属地区<select v-model="form.district" class="select"><option v-for="d in options.districts" :key="d" :value="d">{{ d }}</option><option value="北京市">北京市</option></select></label>
            <label>街道<input v-model="form.street" class="input" /></label>
            <label>详细地址<input v-model="form.address" class="input" style="width: 100%" /></label>
            <label>责任民警<input v-model="form.manager" class="input" /></label>
            <label class="span2">备注<textarea v-model="form.notes" class="input" rows="2" style="width: 100%"></textarea></label>
          </div>
        </div>
        <div class="modal-foot"><button class="btn" @click="showForm = false">取消</button><button class="btn btn-primary" @click="save">保存</button></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { personApi } from '../api'
const baseURL = import.meta.env.VITE_API_BASE || ''
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = 20
const options = ref({ categories: [], risk_levels: [], control_statuses: [], districts: [] })
const filters = reactive({ q: '', category: '', risk_level: '', control_status: '', district: '' })
const showForm = ref(false)
const form = reactive({})
const photoPreview = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))
function fmtTime(t) { if (!t) return ''; return new Date(t).toLocaleString('zh-CN', { hour12: false }) }
function riskClass(r) { return { 高: 'tag-red', 中: 'tag-orange', 低: 'tag-blue' }[r] || 'tag-gray' }
function statusClass(s) { return { 在控: 'tag-green', 待核查: 'tag-orange', 脱管: 'tag-red', 在控就医: 'tag-blue' }[s] || 'tag-gray' }
async function load(p = 1) { page.value = p; const data = await personApi.list({ ...filters, page: page.value, size }); list.value = data.items; total.value = data.total }
function resetFilters() { Object.assign(filters, { q: '', category: '', risk_level: '', control_status: '', district: '' }); load(1) }
function openCreate() { Object.assign(form, { id: null, name: '', id_card: '', gender: '男', age: 30, phone: '', category: '涉稳人员', risk_level: '低', control_status: '在控', district: '', street: '', address: '', manager: '', notes: '', photo: '' }); photoPreview.value = ''; showForm.value = true }
function openEdit(p) { Object.assign(form, JSON.parse(JSON.stringify(p))); photoPreview.value = p.photo; showForm.value = true }
function onPhotoChange(e) { const file = e.target.files[0]; if (!file) return; photoPreview.value = URL.createObjectURL(file); window._pendingPhoto = file }
async function save() { if (!form.name || !form.id_card) { alert('姓名和身份证号为必填'); return } try { let saved; if (form.id) { saved = await personApi.update(form.id, form) } else { saved = await personApi.create(form) } if (window._pendingPhoto) { saved = await personApi.uploadPhoto(saved.id, window._pendingPhoto); window._pendingPhoto = null } showForm.value = false; load(page.value) } catch (e) { alert(e.response?.data?.detail || '保存失败') } }
async function remove(p) { if (!confirm(`确认删除 ${p.name} ？`)) return; await personApi.remove(p.id); load(page.value) }
onMounted(async () => { options.value = await personApi.options(); load(1) })
</script>
<style scoped>
.page-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; } .page-head h2 { font-size: 20px; color: #fff; letter-spacing: 1px; } .head-actions { display: flex; gap: 10px; align-items: center; }
.avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 1px solid rgba(0, 212, 255, 0.4); }
.avatar-empty { display: inline-flex; align-items: center; justify-content: center; background: rgba(0, 212, 255, 0.15); color: var(--accent-cyan); font-weight: 600; }
.empty { text-align: center; color: var(--text-dim); padding: 20px; }
.modal-mask { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.65); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { width: 640px; max-height: 88vh; overflow: auto; background: #0d2547; border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 8px; box-shadow: 0 0 30px rgba(0, 212, 255, 0.2); }
.modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid rgba(0, 212, 255, 0.2); font-size: 16px; font-weight: 600; }
.modal-close { background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; }
.modal-body { padding: 16px 18px; }
.modal-foot { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 18px; border-top: 1px solid rgba(0, 212, 255, 0.2); }
.photo-box { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }
.photo-preview { width: 72px; height: 72px; border-radius: 8px; object-fit: cover; border: 1px dashed rgba(0, 212, 255, 0.5); }
.photo-preview.empty { display: flex; align-items: center; justify-content: center; color: var(--text-dim); font-size: 12px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-grid label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--text-secondary); }
.form-grid .span2 { grid-column: span 2; }
.pagination { display: flex; align-items: center; gap: 16px; margin-top: 14px; justify-content: flex-end; }
.page-btn { background: rgba(0, 212, 255, 0.08); border: 1px solid rgba(0, 212, 255, 0.4); color: var(--accent-cyan); padding: 4px 12px; border-radius: 3px; cursor: pointer; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.text-muted { color: var(--text-dim); font-size: 12px; }
.text-link { color: var(--accent-cyan); cursor: pointer; }
.tag { padding: 2px 8px; border-radius: 3px; font-size: 12px; }
.tag-red { background: rgba(255, 91, 91, 0.2); color: var(--accent-red); } .tag-orange { background: rgba(255, 159, 67, 0.2); color: var(--accent-orange); } .tag-blue { background: rgba(0, 212, 255, 0.2); color: var(--accent-cyan); } .tag-green { background: rgba(46, 230, 168, 0.2); color: var(--accent-green); } .tag-gray { background: rgba(127, 179, 213, 0.2); color: var(--text-secondary); }
</style>