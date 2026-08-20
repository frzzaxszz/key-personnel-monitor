<template>
  <div class="dashboard">
    <div class="bg-grid"></div>
    <header class="dash-header">
      <div class="header-side"><span class="weather-clock">{{ clock }}</span><span class="weather-text">| {{ dateStr }}</span></div>
      <div class="header-title"><span class="title-cn">重点人员综合管控平台</span><span class="title-en">KEY PERSONNEL CONTROL PLATFORM</span></div>
      <nav class="header-nav">
        <router-link to="/dashboard" class="nav-item" :class="{ active: route.path === '/dashboard' }">数据大屏</router-link>
        <router-link to="/persons" class="nav-item" :class="{ active: route.path.startsWith('/persons') }">人员管理</router-link>
        <router-link to="/import" class="nav-item" :class="{ active: route.path === '/import' }">数据导入</router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: route.path === '/settings' }">系统设置</router-link>
      </nav>
    </header>
    <section class="metric-bar">
      <div class="metric-card"><div class="metric-label">重点人员总数</div><div class="metric-value cyan">{{ summary.total }}</div><div class="metric-sub">覆盖 {{ districtCount }} 个地区</div></div>
      <div class="metric-card"><div class="metric-label">高风险人员</div><div class="metric-value red">{{ summary.high_risk }}</div><div class="metric-sub">占比 {{ riskRate }}%</div></div>
      <div class="metric-card"><div class="metric-label">今日新增</div><div class="metric-value gold">{{ summary.today_new }}</div><div class="metric-sub">较昨日 <span class="delta" :class="deltaCls(todayDelta)">{{ fmtDelta(todayDelta) }}</span></div></div>
      <div class="metric-card"><div class="metric-label">在控率</div><div class="metric-value green">{{ summary.control_rate }}<small>%</small></div><div class="metric-sub">在控 {{ controlCount }} 人</div></div>
      <div class="metric-card"><div class="metric-label">待处置预警</div><div class="metric-value orange">{{ summary.pending_alerts }}</div><div class="metric-sub">今日预警 <span class="delta" :class="deltaCls(alertDelta)">{{ fmtDelta(alertDelta) }}</span> · 走访 {{ summary.today_visits }} 次</div></div>
    </section>
    <main class="dash-body">
      <div class="side-col">
        <div class="panel grow1"><div class="panel-title">人员类别构成</div><BaseChart :option="categoryOption" height="100%" :on-events="{ click: onCategoryClick }" /></div>
        <div class="panel grow1"><div class="panel-title">地区人员分布 TOP</div><BaseChart :option="districtOption" height="100%" :on-events="{ click: onDistrictClick }" /></div>
        <div class="panel grow1"><div class="panel-title">管控状态分布</div><BaseChart :option="statusOption" height="100%" :on-events="{ click: onStatusClick }" /></div>
      </div>
      <div class="center-col">
        <div class="panel map-panel">
          <div class="filter-bar" v-if="hasFilter">
            <span class="filter-label">当前筛选：</span>
            <span class="filter-chip" v-if="filters.district">{{ filters.district }}<i class="chip-x" @click="clearFilter('district')">×</i></span>
            <span class="filter-chip" v-if="filters.category">{{ filters.category }}<i class="chip-x" @click="clearFilter('category')">×</i></span>
            <span class="filter-chip" v-if="filters.status">{{ filters.status }}<i class="chip-x" @click="clearFilter('status')">×</i></span>
            <span class="filter-chip" v-if="filters.risk">{{ filters.risk }}风险<i class="chip-x" @click="clearFilter('risk')">×</i></span>
            <button class="back-btn" @click="resetAll">返回全国</button>
          </div>
          <div class="map-legend"><span class="legend-item"><i class="dot high"></i>高风险</span><span class="legend-item"><i class="dot mid"></i>中风险</span><span class="legend-item"><i class="dot low"></i>低风险</span></div>
          <BaseChart :option="mapOption" height="100%" :on-events="{ click: onMapClick }" />
          <div class="map-tip" v-if="mapTip">{{ mapTip }}</div>
          <div class="map-tooltip" v-else>点击地图省份可钻取该地市，点击图表可联动过滤</div>
        </div>
        <div class="center-bottom">
          <div class="panel c-b"><div class="panel-title">风险等级占比</div><BaseChart :option="riskOption" height="100%" :on-events="{ click: onRiskClick }" /></div>
          <div class="panel c-b"><div class="panel-title">近6月新增趋势</div><BaseChart :option="monthlyOption" height="100%" :on-events="{ click: onTimeClick }" /></div>
          <div class="panel c-b"><div class="panel-title">预警类型分布</div><BaseChart :option="alertTypeOption" height="100%" :on-events="{ click: onAlertTypeClick }" /></div>
        </div>
      </div>
      <div class="side-col">
        <div class="panel grow1"><div class="panel-title">近7日新增 / 处置趋势</div><BaseChart :option="trendOption" height="100%" :on-events="{ click: onTimeClick }" /></div>
        <div class="panel grow1"><div class="panel-title">近7日预警趋势</div><BaseChart :option="alertTrendOption" height="100%" :on-events="{ click: onTimeClick }" /></div>
        <div class="panel grow1"><div class="panel-title">实时预警</div>
          <div class="alert-list">
            <div class="alert-item" v-for="(a, i) in summary.alerts" :key="i"><span class="alert-dot" :class="'lv' + (a.alert_level === '高' ? 1 : a.alert_level === '中' ? 2 : 3)"></span><span class="alert-name">{{ a.person_name }}</span><span class="alert-type">{{ a.alert_type }}</span><span class="alert-time">{{ fmtTime(a.created_at) }}</span></div>
            <div class="empty" v-if="!(summary.alerts && summary.alerts.length)">暂无预警</div>
          </div>
        </div>
      </div>
    </main>
    <footer class="dash-footer"><span class="footer-label">实时动态</span><div class="ticker-wrap"><div class="ticker" :style="{ animationDuration: tickerDuration }"><span class="ticker-item" v-for="(v, i) in recentVisits" :key="i"><span class="tick-type" :class="v.type === '预警' ? 'tick-alert' : 'tick-visit'">{{ v.type }}</span>{{ v.content }}</span></div></div></footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import BaseChart from '../components/BaseChart.vue'
import { dashboardApi } from '../api'
import chinaGeo from '../assets/geo/china.json'

const route = useRoute()
const summary = ref({})
const mapData = ref({ districts: {}, points: [] })
const mapTip = ref('')
const recentVisits = ref([])
const filters = ref({ district: '', category: '', status: '', risk: '', alertType: '' })
const hasFilter = computed(() => !!(filters.value.district || filters.value.category || filters.value.status || filters.value.risk))
const loading = ref(false)
const PROVINCE_CENTER = { '北京市':[116.4,39.9],'天津市':[117.2,39.1],'河北省':[114.5,38.0],'山西省':[112.5,37.8],'内蒙古自治区':[111.7,40.8],'辽宁省':[123.4,41.8],'吉林省':[125.3,43.9],'黑龙江省':[126.6,45.8],'上海市':[121.5,31.2],'江苏省':[118.8,32.0],'浙江省':[120.2,30.3],'安徽省':[117.3,31.9],'福建省':[119.3,26.1],'江西省':[115.9,28.7],'山东省':[117.1,36.7],'河南省':[113.7,34.8],'湖北省':[114.3,30.6],'湖南省':[113.0,28.2],'广东省':[113.3,23.1],'广西壮族自治区':[108.3,22.8],'海南省':[110.3,20.0],'重庆市':[106.5,29.5],'四川省':[104.1,30.7],'贵州省':[106.7,26.6],'云南省':[102.7,25.0],'西藏自治区':[91.1,29.7],'陕西省':[108.9,34.3],'甘肃省':[103.8,36.1],'青海省':[101.8,36.6],'宁夏回族自治区':[106.3,38.5],'新疆维吾尔自治区':[87.6,43.8] }
function refreshAll() { const params = {}; if (filters.value.district) params.district = filters.value.district; if (filters.value.category) params.category = filters.value.category; if (filters.value.status) params.status = filters.value.status; if (filters.value.risk) params.risk = filters.value.risk; if (filters.value.alertType) params.alert_type = filters.value.alertType; loading.value = true; return Promise.all([loadSummary(params), loadMap(params)]).finally(() => { loading.value = false }) }
function doDrill(district) { filters.value.district = district; mapTip.value = `已钻取至 ${district}`; refreshAll() }
function clearFilter(key) { filters.value[key] = ''; mapTip.value = ''; refreshAll() }
function resetAll() { filters.value = { district: '', category: '', status: '', risk: '', alertType: '' }; mapTip.value = ''; refreshAll() }
function onMapClick(params) { if (params && params.componentType === 'geo' && params.name) { doDrill(params.name) } }
function onCategoryClick(params) { if (params && params.name !== undefined && params.seriesType === 'pie') { filters.value.category = filters.value.category === params.name ? '' : params.name; refreshAll() } }
function onDistrictClick(params) { if (params && params.name !== undefined && params.name !== '未知') { doDrill(params.name) } }
function onStatusClick(params) { if (params && params.name !== undefined && params.seriesType === 'pie') { filters.value.status = filters.value.status === params.name ? '' : params.name; refreshAll() } }
function onRiskClick(params) { if (params && params.name !== undefined && params.seriesType === 'pie') { filters.value.risk = filters.value.risk === params.name ? '' : params.name; mapTip.value = filters.value.risk ? `已按风险等级「${filters.value.risk}」过滤` : ''; refreshAll() } }
function onAlertTypeClick(params) { if (params && params.name !== undefined) { filters.value.alertType = filters.value.alertType === params.name ? '' : params.name; refreshAll() } }
function onTimeClick(params) { if (params && params.name !== undefined) { mapTip.value = `选中「${params.name}」，时间维度用于展示，不支持过滤人员` } }
const clock = ref('')
const dateStr = ref('')
let timer = null; let tickTimer = null
function updateClock() { const d = new Date(); clock.value = d.toLocaleTimeString('zh-CN', { hour12: false }); dateStr.value = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${'日一二三四五六'[d.getDay()]}` }
updateClock()
function fmtTime(t) { if (!t) return ''; const d = new Date(t); const pad = n => String(n).padStart(2, '0'); return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}` }
const districtCount = computed(() => Object.keys(mapData.value.districts).length || 0)
const riskRate = computed(() => summary.value.total ? ((summary.value.high_risk / summary.value.total) * 100).toFixed(1) : 0)
const controlCount = computed(() => summary.value.total ? Math.round(summary.value.total * summary.value.control_rate / 100) : 0)
const todayDelta = computed(() => (summary.value.today_new || 0) - (summary.value.yesterday_new || 0))
const alertDelta = computed(() => (summary.value.today_alerts || 0) - (summary.value.yesterday_alerts || 0))
const fmtDelta = (d) => d > 0 ? `↑ +${d}` : d < 0 ? `↓ ${d}` : '持平'
const deltaCls = (d) => d > 0 ? 'up' : d < 0 ? 'down' : 'flat'
const PALETTE = ['#00d4ff', '#ffd700', '#ff9f43', '#2ee6a8', '#ff5b5b', '#7d5bff', '#ff7ab8', '#4dd7ff']
const AXIS = { axisLine: { lineStyle: { color: 'rgba(0,212,255,0.3)' } }, axisLabel: { color: '#7fb3d5', fontSize: 11 }, splitLine: { lineStyle: { color: 'rgba(0,212,255,0.1)' } } }
const tooltipBase = { backgroundColor: 'rgba(6,20,40,0.9)', borderColor: 'rgba(0,212,255,0.4)', textStyle: { color: '#e6f7ff', fontSize: 12 } }
const categoryOption = computed(() => ({ color: PALETTE, tooltip: { trigger: 'item', ...tooltipBase, formatter: '{b}: {c} ({d}%)' }, legend: { orient: 'vertical', right: 4, top: 'center', textStyle: { color: '#7fb3d5', fontSize: 11 }, itemWidth: 10, itemHeight: 10 }, series: [{ type: 'pie', radius: ['42%', '68%'], center: ['38%', '50%'], avoidLabelOverlap: true, itemStyle: { borderColor: '#0a1628', borderWidth: 2 }, label: { show: true, color: '#7fb3d5', fontSize: 11, formatter: '{b}\n{c}' }, emphasis: { label: { show: true, fontSize: 13, color: '#fff', formatter: '{b}\n{c}人' } }, data: summary.value.category_data || [] }] }))
const districtOption = computed(() => { const sorted = [...(summary.value.district_data || [])].sort((a, b) => b.value - a.value).slice(0, 8); return { grid: { left: 8, right: 30, top: 8, bottom: 4, containLabel: true }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipBase }, xAxis: { type: 'value', ...AXIS, splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } } }, yAxis: { type: 'category', data: sorted.map(d => d.name).reverse(), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#7fb3d5', fontSize: 11 } }, series: [{ type: 'bar', data: sorted.map(d => d.value).reverse(), barWidth: 12, itemStyle: { borderRadius: [0, 6, 6, 0], color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: 'rgba(0,212,255,0.15)' }, { offset: 1, color: '#00d4ff' }]) }, label: { show: true, position: 'right', color: '#e6f7ff', fontSize: 11 } }] } })
const statusOption = computed(() => { const data = summary.value.status_data || []; return { color: ['#2ee6a8', '#ffd700', '#ff5b5b', '#4dd7ff'], tooltip: { trigger: 'item', ...tooltipBase, formatter: '{b}: {c}人 ({d}%)' }, legend: { bottom: 0, textStyle: { color: '#7fb3d5', fontSize: 11 }, itemWidth: 10, itemHeight: 10 }, series: [{ type: 'pie', radius: ['45%', '70%'], center: ['50%', '44%'], itemStyle: { borderColor: '#0a1628', borderWidth: 2 }, label: { show: true, color: '#7fb3d5', fontSize: 11, formatter: '{b}\n{c}' }, data }] } })
const trendOption = computed(() => ({ color: ['#00d4ff', '#ffd700'], tooltip: { trigger: 'axis', ...tooltipBase }, legend: { top: 0, right: 0, textStyle: { color: '#7fb3d5', fontSize: 11 }, itemWidth: 12 }, grid: { left: 8, right: 12, top: 30, bottom: 4, containLabel: true }, xAxis: { type: 'category', data: (summary.value.trend_data || []).map(d => d.date), ...AXIS }, yAxis: { type: 'value', ...AXIS }, series: [{ name: '新增', type: 'line', smooth: true, data: (summary.value.trend_data || []).map(d => d['新增']), areaStyle: { opacity: 0.15 }, symbolSize: 5, label: { show: true, position: 'top', color: '#00d4ff', fontSize: 10 } }, { name: '处置', type: 'line', smooth: true, data: (summary.value.trend_data || []).map(d => d['处置']), symbolSize: 5, label: { show: true, position: 'bottom', color: '#ffd700' } }] }))
const alertTrendOption = computed(() => { const data = summary.value.alert_trend || []; return { color: ['#ff9f43'], tooltip: { trigger: 'axis', ...tooltipBase }, grid: { left: 8, right: 12, top: 20, bottom: 4, containLabel: true }, xAxis: { type: 'category', data: data.map(d => d.date), ...AXIS }, yAxis: { type: 'value', ...AXIS }, series: [{ name: '预警', type: 'bar', data: data.map(d => d['预警']), barWidth: 14, itemStyle: { borderRadius: [4, 4, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ff9f43' }, { offset: 1, color: 'rgba(255,159,67,0.1)' }]) }, label: { show: true, position: 'top', color: '#ff9f43', fontSize: 10 } }] } })
const riskOption = computed(() => { const data = summary.value.risk_data || []; return { color: ['#ff5b5b', '#ffd700', '#2ee6a8'], tooltip: { trigger: 'item', ...tooltipBase, formatter: '{b}: {c}人 ({d}%)' }, legend: { bottom: 0, textStyle: { color: '#7fb3d5', fontSize: 11 }, itemWidth: 10 }, series: [{ type: 'pie', radius: ['42%', '66%'], center: ['50%', '42%'], itemStyle: { borderColor: '#0a1628', borderWidth: 2 }, label: { show: true, color: '#7fb3d5', fontSize: 11, formatter: '{b}\n{c}' }, data }] } })
const monthlyOption = computed(() => { const data = summary.value.monthly_trend || []; return { color: ['#2ee6a8'], tooltip: { trigger: 'axis', ...tooltipBase }, grid: { left: 8, right: 12, top: 20, bottom: 4, containLabel: true }, xAxis: { type: 'category', data: data.map(d => d.month), ...AXIS }, yAxis: { type: 'value', ...AXIS }, series: [{ name: '新增', type: 'line', smooth: true, data: data.map(d => d['新增']), areaStyle: { opacity: 0.15 }, symbolSize: 5, label: { show: true, position: 'top', color: '#2ee6a8', fontSize: 10 } }] } })
const alertTypeOption = computed(() => { const data = summary.value.alert_type_data || []; return { color: PALETTE, tooltip: { trigger: 'item', ...tooltipBase, formatter: '{b}: {c} ({d}%)' }, legend: { type: 'scroll', bottom: 0, textStyle: { color: '#7fb3d5', fontSize: 10 }, itemWidth: 8, itemHeight: 8 }, series: [{ name: '预警分布', type: 'pie', radius: ['40%', '62%'], center: ['50%', '42%'], itemStyle: { borderColor: '#0a1628', borderWidth: 2 }, avoidLabelOverlap: true, label: { show: true, color: '#7fb3d5', fontSize: 10, formatter: '{b}\n{c}' }, emphasis: { label: { show: true, color: '#fff', fontSize: 11, formatter: '{b}\n{c}' } }, data: data.slice(0, 6) }] } })
const mapOption = computed(() => { const districtVals = mapData.value.districts || {}; const maxV = Math.max(1, ...Object.values(districtVals)); const regions = Object.entries(districtVals).map(([name, value]) => { const ratio = value / maxV; let color = 'rgba(13, 60, 110, 0.5)'; if (ratio > 0.6) color = 'rgba(255, 91, 91, 0.55)'; else if (ratio > 0.3) color = 'rgba(255, 159, 67, 0.5)'; else if (ratio > 0) color = 'rgba(0, 212, 255, 0.45)'; return { name, itemStyle: { areaColor: color } }; }); const center = filters.value.district ? PROVINCE_CENTER[filters.value.district] : undefined; const zoom = filters.value.district ? 2.6 : 1.15; const points = (mapData.value.points || []); const pointData = points.map(p => ({ name: p.name, value: [p.longitude, p.latitude, p.risk_level === '高' ? 16 : p.risk_level === '中' ? 10 : 6], risk: p.risk_level, person: p })); const series = []; if (pointData.length) { series.push({ name: '人员', type: 'effectScatter', coordinateSystem: 'geo', zlevel: 3, rippleEffect: { scale: 3, brushType: 'stroke' }, symbolSize: v => (v[2] || 6), itemStyle: { color: p => p.data.risk === '高' ? '#ff5b5b' : p.data.risk === '中' ? '#ffd700' : '#00d4ff' }, data: pointData, tooltip: { formatter: p => { const d = p.data.person; return `${d.name}<br/>类别：${d.category}<br/>风险：${d.risk_level}<br/>地区：${d.district}` } } }) }; const geo = { map: 'china', roam: true, zoom, center, label: { show: false }, itemStyle: { areaColor: 'rgba(13, 60, 110, 0.5)', borderColor: 'rgba(0, 212, 255, 0.6)', borderWidth: 1, shadowColor: 'rgba(0, 212, 255, 0.2)', shadowBlur: 10 }, emphasis: { itemStyle: { areaColor: 'rgba(0, 168, 204, 0.6)' }, label: { show: false } }, regions }; return { tooltip: { ...tooltipBase, trigger: 'item' }, geo, series } })
const tickerDuration = computed(() => `${Math.max(recentVisits.value.length * 8, 24)}s`)
async function loadSummary(params = {}) { try { summary.value = await dashboardApi.summary(params); recentVisits.value = [...(summary.value.alerts || []).map(a => ({ type: '预警', content: `${a.district} ${a.person_name}：${a.content}` })), ...(summary.value.recent_visits || []).map(v => ({ type: '动态', content: `${v.district || ''} ${v.person_name || ''}：${v.content}（${v.manager}）` }))] } catch (e) { console.error(e) } }
async function loadMap(params = {}) { try { mapData.value = await dashboardApi.map(params) } catch (e) { console.error(e) } }
echarts.registerMap('china', chinaGeo)
onMounted(() => { refreshAll(); timer = setInterval(updateClock, 1000); tickTimer = setInterval(() => { refreshAll() }, 15000) })
onBeforeUnmount(() => { clearInterval(timer); clearInterval(tickTimer) })
</script>

<style scoped>
.dashboard { position: relative; width: 100vw; height: 100vh; background: radial-gradient(ellipse at 50% 0%, #0e2a4d 0%, #0a1628 60%); display: flex; flex-direction: column; overflow: hidden; }
.bg-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px); background-size: 40px 40px; pointer-events: none; }
.dash-header { position: relative; z-index: 2; display: flex; align-items: center; justify-content: space-between; height: 64px; padding: 0 24px; border-bottom: 1px solid rgba(0,212,255,0.25); background: linear-gradient(180deg, rgba(0,50,100,0.35), transparent); }
.header-title { text-align: center; flex: 1; }
.title-cn { display: block; font-size: 26px; font-weight: 700; letter-spacing: 6px; background: linear-gradient(180deg, #ffffff, #8ee8ff); -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: 0 0 30px rgba(0,212,255,0.5); }
.title-en { display: block; font-size: 10px; letter-spacing: 4px; color: rgba(0,212,255,0.6); margin-top: 2px; }
.header-side { width: 200px; font-size: 13px; color: var(--text-secondary); }
.header-nav { display: flex; gap: 6px; }
.nav-item { color: var(--text-secondary); text-decoration: none; font-size: 13px; padding: 6px 14px; border: 1px solid transparent; border-radius: 3px; transition: all 0.2s; }
.nav-item:hover { color: var(--accent-cyan); }
.nav-item.active { color: #fff; border-color: rgba(0,212,255,0.5); background: rgba(0,212,255,0.15); box-shadow: 0 0 10px rgba(0,212,255,0.3); }
.metric-bar { position: relative; z-index: 2; display: flex; gap: 14px; padding: 12px 20px; justify-content: center; }
.metric-card { flex: 1; max-width: 240px; text-align: center; padding: 10px 8px; background: var(--bg-panel); border: 1px solid rgba(0,212,255,0.2); border-radius: 4px; position: relative; }
.metric-card::after { content: ""; position: absolute; bottom: -1px; left: 20%; right: 20%; height: 2px; background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent); }
.metric-label { font-size: 12px; color: var(--text-secondary); letter-spacing: 1px; }
.metric-value { font-size: 34px; font-weight: 700; font-family: 'Consolas', 'Courier New', monospace; line-height: 1.2; text-shadow: 0 0 18px currentColor; }
.metric-value.cyan { color: var(--accent-cyan); } .metric-value.red { color: var(--accent-red); } .metric-value.gold { color: var(--accent-gold); } .metric-value.green { color: var(--accent-green); } .metric-value.orange { color: var(--accent-orange); }
.metric-value small { font-size: 18px; }
.metric-sub { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
.delta { font-weight: 600; } .delta.up { color: #ff6b6b; } .delta.down { color: #2ee6a8; } .delta.flat { color: #7fb3d5; }
.dash-body { position: relative; z-index: 2; flex: 1; display: flex; gap: 14px; padding: 0 20px 12px; min-height: 0; }
.side-col { width: 27%; display: flex; flex-direction: column; gap: 14px; }
.center-col { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 14px; min-height: 0; }
.grow1 { flex: 1; min-height: 0; }
.side-col .panel { display: flex; flex-direction: column; } .side-col .panel :deep(.chart) { flex: 1; min-height: 0; }
.map-panel { flex: 1; min-height: 0; position: relative; } .map-panel :deep(.chart) { height: 100%; }
.center-bottom { display: flex; gap: 14px; height: 30%; flex-shrink: 0; min-height: 0; } .center-bottom .c-b { flex: 1; min-width: 0; } .c-b { display: flex; flex-direction: column; } .c-b :deep(.chart) { flex: 1; min-height: 0; }
.filter-bar { position: absolute; top: 10px; left: 16px; z-index: 6; display: flex; align-items: center; gap: 8px; background: rgba(6,20,40,0.75); padding: 5px 12px; border-radius: 4px; border: 1px solid rgba(0,212,255,0.25); }
.filter-label { font-size: 12px; color: var(--text-dim); } .filter-chip { font-size: 12px; color: var(--accent-cyan); background: rgba(0,212,255,0.12); padding: 2px 8px; border-radius: 3px; } .chip-x { cursor: pointer; margin-left: 5px; color: var(--text-secondary); } .chip-x:hover { color: #fff; }
.back-btn { font-size: 12px; color: #fff; background: var(--accent-blue, #0a5bd3); border: none; border-radius: 3px; padding: 3px 12px; cursor: pointer; } .back-btn:hover { background: var(--accent-cyan); color: #02122a; }
.map-legend { position: absolute; top: 10px; right: 16px; z-index: 5; display: flex; gap: 12px; background: rgba(6,20,40,0.6); padding: 4px 10px; border-radius: 3px; } .legend-item { font-size: 12px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px; } .legend-item .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; } .dot.high { background: var(--accent-red); box-shadow: 0 0 6px var(--accent-red); } .dot.mid { background: var(--accent-gold); box-shadow: 0 0 6px var(--accent-gold); } .dot.low { background: var(--accent-cyan); box-shadow: 0 0 6px var(--accent-cyan); }
.map-tip { position: absolute; left: 14px; bottom: 12px; z-index: 5; font-size: 12px; color: var(--accent-cyan); }
.alert-list { overflow: auto; flex: 1; min-height: 0; }
.alert-item { display: flex; align-items: center; gap: 6px; padding: 7px 4px; border-bottom: 1px dashed rgba(0,212,255,0.15); font-size: 12px; } .alert-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; } .alert-dot.lv1 { background: var(--accent-red); box-shadow: 0 0 6px var(--accent-red); } .alert-dot.lv2 { background: var(--accent-gold); box-shadow: 0 0 6px var(--accent-gold); } .alert-dot.lv3 { background: var(--accent-cyan); box-shadow: 0 0 6px var(--accent-cyan); } .alert-name { color: #fff; font-weight: 600; } .alert-type { color: var(--accent-orange); } .alert-time { margin-left: auto; color: var(--text-dim); font-size: 11px; }
.empty { color: var(--text-dim); text-align: center; padding: 20px; font-size: 12px; }
.dash-footer { position: relative; z-index: 2; display: flex; align-items: center; height: 36px; border-top: 1px solid rgba(0,212,255,0.2); background: linear-gradient(180deg, transparent, rgba(0,50,100,0.3)); padding: 0 20px; } .footer-label { color: var(--accent-gold); font-size: 13px; font-weight: 600; margin-right: 16px; white-space: nowrap; letter-spacing: 2px; } .ticker-wrap { flex: 1; overflow: hidden; } .ticker { display: inline-block; white-space: nowrap; animation: ticker-scroll linear infinite; will-change: transform; } .ticker-item { font-size: 12px; color: var(--text-secondary); margin-right: 40px; } .tick-type { padding: 1px 6px; border-radius: 2px; font-size: 11px; margin-right: 6px; } .tick-alert { background: rgba(255,91,91,0.2); color: var(--accent-red); } .tick-visit { background: rgba(0,212,255,0.2); color: var(--accent-cyan); } @keyframes ticker-scroll { from { transform: translateX(100vw); } to { transform: translateX(-100%); } }
</style>