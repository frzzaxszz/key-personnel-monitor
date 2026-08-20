<template>
  <div class="admin-page">
    <div class="page-head"><h2>系统设置</h2><div class="head-actions"><router-link to="/dashboard" class="btn">← 返回大屏</router-link></div></div>
    <div class="admin-card" style="margin-bottom: 16px">
      <h4>数据库连接配置</h4>
      <p class="text-muted" style="margin: 8px 0 14px">当前使用 SQLite 本地存储。如需连接 MySQL 数据库，填写连接信息后点击"测试并切换连接"。</p>
      <div class="form-grid">
        <label>数据库类型<select v-model="form.db_type" class="select"><option value="sqlite">SQLite（本地）</option><option value="mysql">MySQL</option></select></label>
        <label>主机地址<input v-model="form.host" class="input" :disabled="form.db_type === 'sqlite'" /></label>
        <label>端口<input v-model.number="form.port" type="number" class="input" :disabled="form.db_type === 'sqlite'" /></label>
        <label>数据库名<input v-model="form.database" class="input" :disabled="form.db_type === 'sqlite'" /></label>
        <label>用户名<input v-model="form.username" class="input" :disabled="form.db_type === 'sqlite'" /></label>
        <label>密码<input v-model="form.password" type="password" class="input" :disabled="form.db_type === 'sqlite'" /></label>
      </div>
      <div style="display: flex; gap: 10px; margin-top: 14px">
        <button class="btn btn-primary" @click="testAndSwitch">测试并切换连接</button><span v-if="connMsg" class="text-muted" :style="{ color: connOk ? 'var(--accent-green)' : 'var(--accent-red)' }">{{ connMsg }}</span>
      </div>
    </div>
    <div class="admin-card" style="margin-bottom: 16px">
      <h4>自动更新设置</h4>
      <p class="text-muted" style="margin: 8px 0 14px">开启后，系统将按设定间隔自动生成实时动态与预警，用于大屏演示；连接外部数据库后可用于定时同步数据。</p>
      <div class="auto-row">
        <label class="switch-label"><input type="checkbox" v-model="form.auto_sync" class="switch" /><span>启用自动更新</span></label>
        <label style="display: flex; align-items: center; gap: 8px"><span class="text-muted">更新间隔</span><input v-model.number="form.sync_interval" type="number" min="10" class="input" style="width: 90px" /><span class="text-muted">秒</span></label>
        <button class="btn btn-primary" @click="saveSettings">保存设置</button>
      </div>
    </div>
    <div class="admin-card">
      <h4 style="margin-bottom: 10px">系统说明</h4>
      <ul class="info-list"><li>大屏数据每 15 秒自动刷新，实时动态在底部滚动展示。</li><li>人员管理支持新增、编辑、删除、上传照片、添加走访记录。</li><li>数据导入支持 Excel 模板批量导入与导出。</li><li>数据默认存储于 backend/data/app.db（SQLite），可切换 MySQL 连接。</li></ul>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { settingsApi } from '../api'
const form = reactive({})
const connMsg = ref('')
const connOk = ref(false)
async function load() { Object.assign(form, await settingsApi.get()) }
async function testAndSwitch() { connMsg.value = '正在测试连接…'; connOk.value = false; try { const r = await settingsApi.test(); connOk.value = true; connMsg.value = r.message; await settingsApi.update(form) } catch (e) { connOk.value = false; connMsg.value = e.response?.data?.detail || '连接失败' } }
async function saveSettings() { await settingsApi.update(form); connMsg.value = '已保存'; connOk.value = true }
onMounted(load)
</script>
<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-head h2 { font-size: 20px; }
.head-actions { display: flex; gap: 10px; }
.form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.form-grid label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--text-secondary); }
.auto-row { display: flex; align-items: center; gap: 20px; }
.switch-label { display: flex; align-items: center; gap: 6px; font-size: 14px; }
.info-list { padding-left: 18px; }
.info-list li { font-size: 13px; color: var(--text-secondary); margin: 6px 0; }
</style>