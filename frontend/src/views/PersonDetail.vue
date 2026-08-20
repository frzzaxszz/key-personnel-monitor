<template>
  <div class="admin-page">
    <div class="page-head">
      <h2>人员详情</h2>
      <div class="head-actions">
        <router-link to="/persons" class="btn">← 返回列表</router-link>
        <router-link to="/dashboard" class="btn">大屏</router-link>
      </div>
    </div>
    <div class="detail-wrap" v-if="person">
      <div class="admin-card profile-card">
        <div class="profile-left">
          <div class="photo-wrap">
            <img v-if="person.photo" :src="person.photo" class="big-photo" />
            <div v-else class="big-photo empty">{{ person.name[0] }}</div>
            <button class="btn" style="width: 100%; margin-top: 10px" @click="triggerUpload">上传照片</button>
            <input type="file" ref="fileInput" accept="image/*" hidden @change="uploadPhoto" />
          </div>
        </div>
        <div class="profile-right">
          <h3 class="p-name">{{ person.name }}<span class="tag" :class="riskClass(person.risk_level)">风险 {{ person.risk_level }}</span><span class="tag" :class="statusClass(person.control_status)">{{ person.control_status }}</span></h3>
          <table class="info-table">
            <tr><td>身份证号</td><td>{{ person.id_card }}</td><td>性别</td><td>{{ person.gender }}</td></tr>
            <tr><td>年龄</td><td>{{ person.age }}</td><td>手机号</td><td>{{ person.phone }}</td></tr>
            <tr><td>人员类别</td><td>{{ person.category }}</td><td>所属地区</td><td>{{ person.district }}</td></tr>
            <tr><td>街道</td><td>{{ person.street }}</td><td>责任民警</td><td>{{ person.manager }}</td></tr>
            <tr><td>详细地址</td><td colspan="3">{{ person.address }}</td></tr>
            <tr><td>备注</td><td colspan="3">{{ person.notes || '—' }}</td></tr>
            <tr><td>入库时间</td><td>{{ fmtTime(person.created_at) }}</td><td>更新时间</td><td>{{ fmtTime(person.updated_at) }}</td></tr>
          </table>
          <div class="profile-actions"><button class="btn btn-primary" @click="editMode = !editMode">{{ editMode ? '取消编辑' : '编辑信息' }}</button></div>
        </div>
      </div>
      <div class="admin-card" v-if="editMode">
        <h4 style="margin-bottom: 12px">编辑人员信息</h4>
        <div class="form-grid">
          <label>姓名 *<input v-model="form.name" class="input" /></label>
          <label>身份证号 *<input v-model="form.id_card" class="input" /></label>
          <label>性别<select v-model="form.gender" class="select"><option>男</option><option>女</option></select></label>
          <label>年龄<input v-model.number="form.age" type="number" class="input" /></label>
          <label>手机号<input v-model="form.phone" class="input" /></label>
          <label>人员类别<select v-model="form.category" class="select"><option v-for="c in options.categories" :key="c">{{ c }}</option></select></label>
          <label>风险等级<select v-model="form.risk_level" class="select"><option v-for="r in options.risk_levels" :key="r">{{ r }}</option></select></label>
          <label>管控状态<select v-model="form.control_status" class="select"><option v-for="s in options.control_statuses" :key="s">{{ s }}</option></select></label>
          <label>所属地区<input v-model="form.district" class="input" /></label>
          <label>街道<input v-model="form.street" class="input" /></label>
          <label>详细地址<input v-model="form.address" class="input" /></label>
          <label>责任民警<input v-model="form.manager" class="input" /></label>
          <label class="span2">备注<textarea v-model="form.notes" class="input" rows="2"></textarea></label>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 14px"><button class="btn btn-primary" @click="saveEdit">保存修改</button></div>
      </div>
      <div class="admin-card">
        <h4 style="margin-bottom: 12px">走访 / 处置记录</h4>
        <div class="visit-form">
          <textarea v-model="visitContent" class="input" placeholder="填写走访记录内容…" rows="2" style="flex: 1"></textarea>
          <button class="btn btn-primary" @click="addVisit">添加记录</button>
        </div>
        <table class="grid-table" style="margin-top: 12px">
          <thead><tr><th>时间</th><th>内容</th><th>责任民警</th></tr></thead>
          <tbody><tr v-for="v in visits" :key="v.id"><td>{{ fmtTime(v.visit_date) }}</td><td>{{ v.content }}</td><td>{{ v.manager }}</td></tr><tr v-if="!visits.length"><td colspan="3" class="empty">暂无记录</td></tr></tbody>
        </table>
      </div>
    </div>
    <div v-else class="loading">加载中…</div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { personApi } from '../api'
const route = useRoute()
const person = ref(null)
const visits = ref([])
const options = ref({ categories: [], risk_levels: [], control_statuses: [] })
const editMode = ref(false)
const form = reactive({})
const visitContent = ref('')
const fileInput = ref(null)
function fmtTime(t) { if (!t) return ''; return new Date(t).toLocaleString('zh-CN', { hour12: false }) }
function riskClass(r) { return { 高: 'tag-red', 中: 'tag-orange', 低: 'tag-blue' }[r] || 'tag-gray' }
function statusClass(s) { return { 在控: 'tag-green', 待核查: 'tag-orange', 脱管: 'tag-red', 在控就医: 'tag-blue' }[s] || 'tag-gray' }
async function load() { const id = route.params.id; person.value = await personApi.get(id); visits.value = await personApi.visits(id); Object.assign(form, JSON.parse(JSON.stringify(person.value))) }
function triggerUpload() { fileInput.value.click() }
async function uploadPhoto(e) { const file = e.target.files[0]; if (!file) return; await personApi.uploadPhoto(person.value.id, file); await load() }
async function saveEdit() { await personApi.update(person.value.id, form); editMode.value = false; await load() }
async function addVisit() { if (!visitContent.value.trim()) return; await personApi.addVisit(person.value.id, { content: visitContent.value, manager: form.manager || '系统' }); visitContent.value = ''; visits.value = await personApi.visits(person.value.id) }
onMounted(async () => { options.value = await personApi.options(); load() })
</script>
<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-head h2 { font-size: 20px; }
.head-actions { display: flex; gap: 10px; }
.detail-wrap { display: flex; flex-direction: column; gap: 16px; max-width: 1080px; }
.profile-card { display: flex; gap: 24px; }
.profile-left { width: 180px; }
.big-photo { width: 180px; height: 220px; border-radius: 8px; object-fit: cover; border: 1px solid rgba(0,212,255,0.5); }
.big-photo.empty { display: flex; align-items: center; justify-content: center; font-size: 60px; font-weight: 700; color: var(--accent-cyan); background: rgba(0,212,255,0.08); }
.profile-right { flex: 1; }
.p-name { font-size: 22px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
.info-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.info-table td { padding: 8px 10px; border-bottom: 1px dashed rgba(0,212,255,0.12); }
.info-table td:first-child, .info-table td:nth-child(3) { color: var(--text-secondary); width: 90px; white-space: nowrap; }
.profile-actions { margin-top: 16px; }
.visit-form { display: flex; gap: 10px; }
.loading { color: var(--text-dim); text-align: center; padding: 40px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-grid label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--text-secondary); }
.form-grid .span2 { grid-column: span 2; }
</style>