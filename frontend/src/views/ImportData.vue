<template>
  <div class="admin-page">
    <div class="page-head">
      <h2>数据导入</h2>
      <div class="head-actions"><router-link to="/dashboard" class="btn">← 返回大屏</router-link></div>
    </div>
    <div class="admin-card import-card">
      <h4>Excel 批量导入重点人员</h4>
      <p class="text-muted" style="margin: 8px 0 14px">请先下载模板，按照模板格式填写数据后上传。身份证号重复的数据将被跳过并记录错误。</p>
      <div class="import-actions">
        <a class="btn btn-gold" :href="`${baseURL}/api/import/template`">下载导入模板</a>
        <label class="btn btn-primary" style="cursor: pointer">选择 Excel 文件<input type="file" accept=".xlsx,.xls" hidden @change="doImport" /></label>
      </div>
      <div v-if="result" class="import-result" :class="result.failed ? 'has-fail' : 'ok'">
        <div class="result-row"><span>共 <b>{{ result.total }}</b> 条</span><span>成功 <b style="color: var(--accent-green)">{{ result.success }}</b> 条</span><span v-if="result.failed">失败 <b style="color: var(--accent-red)">{{ result.failed }}</b> 条</span></div>
        <div v-if="result.errors && result.errors.length" class="error-list"><div v-for="(e, i) in result.errors" :key="i" class="error-item">{{ e }}</div></div>
      </div>
    </div>
    <div class="admin-card">
      <h4 style="margin-bottom: 12px">导入记录</h4>
      <table class="grid-table">
        <thead><tr><th>时间</th><th>文件名</th><th>总数</th><th>成功</th><th>失败</th></tr></thead>
        <tbody><tr v-for="l in logs" :key="l.id"><td>{{ fmtTime(l.created_at) }}</td><td>{{ l.filename }}</td><td>{{ l.total }}</td><td style="color: var(--accent-green)">{{ l.success }}</td><td style="color: var(--accent-red)">{{ l.failed }}</td></tr><tr v-if="!logs.length"><td colspan="5" class="empty">暂无导入记录</td></tr></tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { importApi } from '../api'
const baseURL = import.meta.env.VITE_API_BASE || ''
const result = ref(null)
const logs = ref([])
function fmtTime(t) { return t ? new Date(t).toLocaleString('zh-CN', { hour12: false }) : '' }
async function doImport(e) { const file = e.target.files[0]; if (!file) return; result.value = null; try { result.value = await importApi.upload(file) } catch (err) { alert(err.response?.data?.detail || '导入失败') } e.target.value = ''; loadLogs() }
async function loadLogs() { logs.value = await importApi.logs() }
onMounted(loadLogs)
</script>
<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-head h2 { font-size: 20px; }
.head-actions { display: flex; gap: 10px; }
.import-card { margin-bottom: 16px; }
.import-actions { display: flex; gap: 12px; }
.import-result { margin-top: 14px; padding: 12px; border-radius: 6px; background: rgba(0,212,255,0.06); }
.import-result.has-fail { background: rgba(255,91,91,0.06); }
.result-row { display: flex; gap: 24px; font-size: 14px; }
.error-list { margin-top: 10px; max-height: 160px; overflow: auto; }
.error-item { font-size: 12px; color: var(--accent-red); padding: 2px 0; }
.empty { text-align: center; color: var(--text-dim); padding: 16px; }
</style>