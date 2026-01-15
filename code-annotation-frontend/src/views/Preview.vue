<template>
  <div class="app" :style="{gridTemplateColumns: (leftCollapsed? '0px' : '320px') + ' 1fr ' + ((codeCollapsed && !chatOnly)? '0px' : '320px')}">
    <header class="topbar">
      <div class="brand">
        <div class="logo">Q</div>
        <div class="title">分类分析演示</div>
      </div>
      <div class="top-actions">
        <input type="file" id="file-input" style="display:none" @change="handleUpload" />
        <button class="btn ghost" v-if="leftCollapsed" @click="toggleLeft">▸ 展开左侧</button>
        <button class="btn ghost" v-if="codeCollapsed" @click="toggleCode">▸ 展开预览</button>
        <button class="btn ghost" @click="triggerUpload">上传文件</button>
        <button class="btn ghost" @click="downloadReport">下载报告</button>
        <button class="btn ghost" @click="toggleChatOnly">{{ chatOnly? '全布局':'仅对话' }}</button>
        <button class="btn ghost" @click="toggleTheme">{{ theme==='light'?'🌙 暗色':'☀️ 亮色' }}</button>
      </div>
    </header>
    <header-nav :current="'code'" />

    <aside class="left" v-show="!leftCollapsed">
      <div class="panel-title strong">
        <span>功能区</span>
        <button class="icon-btn" @click="toggleLeft">{{ leftCollapsed? '▸ 展开左侧':'▾ 收起左侧' }}</button>
      </div>
      <section class="panel">
        <div class="panel-title">文件浏览</div>
        <div class="file-tree">
          <div v-for="node in fileTree" :key="node.id" class="tree-node">
            <div class="node-label" :class="{active: selectedFilePath===node.path}" @click="node.type==='dir'?toggleDir(node):selectFile(node)">
              <span class="node-icon" v-if="node.type==='dir'">{{ node.expanded? '📂' : '📁' }}</span>
              <span class="node-icon" v-else>📄</span>
              <span>{{ node.name }}</span>
            </div>
            <div v-if="node.children && node.children.length && node.expanded" class="node-children">
              <div v-for="child in node.children" :key="child.id" class="tree-node">
                <div class="node-label" :class="{active: selectedFilePath===child.path}" @click="selectFile(child)">
                  <span class="node-icon" v-if="child.type==='dir'">📁</span>
                  <span class="node-icon" v-else>📄</span>
                  <span>{{ child.name }}</span>
                  <button class="icon-btn" style="margin-left:auto" v-if="child.type==='file' && child.path && child.path.startsWith('uploaded/')" @click.stop="deleteFile(child)">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </aside>

    <main class="center">
      <section class="code" v-show="!codeCollapsed">
        <div class="code-toolbar">
          <div class="path">{{ selectedFilePath }}</div>
          <div class="tools">
            <button class="icon-btn" @click="toggleCode">{{ codeCollapsed? '▸ 展开预览':'▾ 收起预览' }}</button>
            <input class="search" v-model="searchTextRaw" @keyup.enter="send" placeholder="搜索代码关键字" />
            <button class="icon-btn" @click="fontUp">A+</button>
            <button class="icon-btn" @click="fontDown">A-</button>
            <button class="icon-btn" @click="copyCode">复制代码</button>
          </div>
        </div>
        <div class="code-view" :style="{fontSize: fontSize+'px'}" v-show="!codeCollapsed">
          <div class="code-lines">
            <div v-for="(line,i) in filteredCode" :key="i" class="code-line" :class="lineClass(line)" :id="line.fn ? ('line-'+line.fn) : null">
              <div class="label" :class="labelClass(line)">{{ lineLabel(line) }}</div>
              <div class="gutter">{{ i+1 }}</div>
              <pre class="content"><code :class="'language-'+currentLang">{{ line.text }}</code></pre>
            </div>
            <div v-if="filteredCode.length===0" class="empty">未匹配到结果</div>
          </div>
        </div>
      </section>
    </main>

    <aside class="right" v-show="chatOnly || !codeCollapsed">
      <section class="panel">
        <div class="panel-title strong">
          <span>分类结果统计</span>
          <div class="panel-actions">
            <button class="icon-btn" @click="refreshStats">刷新</button>
          </div>
        </div>
        <div class="bar-chart">
          <div class="bar-row" v-for="b in barData" :key="b.key">
            <div class="bar-label">{{ b.label }}</div>
            <div class="bar-track">
              <div class="bar" :style="{width: b.percent+'%', background: b.color}"></div>
            </div>
            <div class="bar-count">{{ b.count }}</div>
          </div>
          <div class="bar-note">总行数：{{ totalLines }}；有标签行：{{ taggedLines }}</div>
        </div>
      </section>
      <section class="chat" style="margin-top:12px">
        <div class="section-title">自然语言需求输入</div>
        <div class="chat-history">
          <div class="msg user">
            <div class="avatar">👤</div>
            <div class="bubble">帮我分类 arm/driver.c 的 function 级别，只显示 riscv 相关函数</div>
          </div>
          <div class="msg system">
            <div class="avatar">🅆</div>
            <div class="bubble">已接收需求，正在分析 arm/driver.c 的 function 级别分类，目标架构：riscv</div>
          </div>
          <div class="msg" v-for="m in messages" :key="m.id" :class="m.role">
            <div class="avatar">{{ m.role==='user'?'👤':'🅆' }}</div>
            <div class="bubble">{{ m.text }}</div>
          </div>
        </div>
        <div class="chat-input">
          <textarea v-model="inputText" class="textarea" rows="1" @keydown.enter="onEnter" placeholder="请输入分类需求"></textarea>
          <button class="btn primary" @click="send">发送</button>
        </div>
      </section>
    </aside>
    <div class="toast" v-if="toastVisible">{{ toastText }}</div>
  </div>
</template>
<script>
import Prism from 'prismjs'
import HeaderNav from '@/components/HeaderNav.vue'

const sampleCode = {
  'arm/driver.c': [
    { text: '#include <stdio.h>', tags: [] },
    { text: 'int init_driver() {', tags: ['arm'], type: 'function', fn: 'init_driver' },
    { text: '    int ok = 1;', tags: ['arm'] },
    { text: '    return ok;', tags: ['arm'] },
    { text: '}', tags: ['arm'] },
    { text: '', tags: [] },
    { text: 'int calc_riscv(int x) {', tags: ['riscv'], type: 'function', fn: 'calc_riscv' },
    { text: '    int res = x;', tags: ['riscv'] },
    { text: '    if (RISCV_VECTOR) {', tags: ['riscv'], type: 'block' },
    { text: '        res += 8;', tags: ['riscv'] },
    { text: '    }', tags: ['riscv'] },
    { text: '    return res;', tags: ['riscv'], type: 'stmt' },
    { text: '}', tags: ['riscv'] },
    { text: '', tags: [] },
    { text: 'void print_info() {', tags: ['common'], type: 'function', fn: 'print_info' },
    { text: '    printf("info\\n");', tags: ['common'] },
    { text: '}', tags: ['common'] }
  ],
  'arm/global.h': [
    { text: '#pragma once', tags: [] },
    { text: '#define RISCV_VECTOR 1', tags: [] }
  ]
}

export default {
  components: { HeaderNav },
  data() {
    return {
      fileTree: [
        { id: 'root-arm', name: 'arm', type: 'dir', path: 'arm', expanded: true, children: [
          { id: 'arm-driver', name: 'driver.c', type: 'file', path: 'arm/driver.c' },
          { id: 'arm-global', name: 'global.h', type: 'file', path: 'arm/global.h' }
        ]}
      ],
      selectedFilePath: 'arm/driver.c',
      fontSize: 14,
      messages: [],
      inputText: '',
      searchText: '',
      searchTextRaw: '',
      _searchTimer: null,
      toastText: '',
      toastVisible: false,
      codeCollapsed: false,
      leftCollapsed: false,
      chatOnly: false,
      reportData: null,
      uploadedFiles: [],
      apiBase: 'http://127.0.0.1:5000',
      lastZipFile: null,
      config: { granularity: 'function', level: 'ISA', targetArch: 'all' },
      theme: 'light',
      codeTextMap: {},
      serverStats: null,
      lastReply: ''
    }
  },
  computed: {
    currentCode() { return sampleCode[this.selectedFilePath] || [] },
    filteredCode() {
      const text = this.searchText.trim().toLowerCase()
      if (!text) return this.currentCode
      return this.currentCode.filter(l => (l.text || '').toLowerCase().includes(text))
    },
    stats() {
      if (this.serverStats) return this.serverStats
      const lines = this.currentCode
      const funcs = lines.filter(l => l.type === 'function')
      const funcCount = funcs.length
      const riscvFuncCount = funcs.filter(l => (l.tags || []).includes('riscv')).length
      let fileArch = '通用'
      const hasArm = lines.some(l => (l.tags || []).includes('arm'))
      const hasRiscv = lines.some(l => (l.tags || []).includes('riscv'))
      if (hasArm && hasRiscv) fileArch = '混合'
      else if (hasArm) fileArch = 'arm'
      else if (hasRiscv) fileArch = 'riscv'
      return { funcCount, riscvFuncCount, fileArch }
    },
    totalLines() { return this.currentCode.length },
    taggedLines() { return this.currentCode.filter(l => (l.tags||[]).length).length },
    barData() {
      if (this.serverStats && this.serverStats.counts) {
        const counts = this.serverStats.counts
        const total = Math.max(1, (counts.arm||0)+(counts.riscv||0)+(counts.common||0))
        const toPercent = (n) => Math.round((n/total)*100)
        return [
          { key:'arm', label:'arm', count:counts.arm||0, percent:toPercent(counts.arm||0), color:'var(--arm-color, #4da3ff)' },
          { key:'riscv', label:'riscv', count:counts.riscv||0, percent:toPercent(counts.riscv||0), color:'var(--riscv-color, #5ccf73)' },
          { key:'common', label:'通用', count:counts.common||0, percent:toPercent(counts.common||0), color:'#b0b0b0' }
        ]
      }
      const lines = this.currentCode
      const countArm = lines.filter(l => (l.tags||[]).includes('arm')).length
      const countRiscv = lines.filter(l => (l.tags||[]).includes('riscv')).length
      const countCommon = lines.filter(l => (l.tags||[]).includes('common')).length
      const total = Math.max(1, lines.length)
      const toPercent = (n) => Math.round((n/total)*100)
      return [
        { key:'arm', label:'arm', count:countArm, percent:toPercent(countArm), color:'var(--arm-color, #4da3ff)' },
        { key:'riscv', label:'riscv', count:countRiscv, percent:toPercent(countRiscv), color:'var(--riscv-color, #5ccf73)' },
        { key:'common', label:'通用', count:countCommon, percent:toPercent(countCommon), color:'#b0b0b' }
      ]
    },
    currentLang() {
      const p = this.selectedFilePath || ''
      const ext = p.split('.').pop().toLowerCase()
      if (['c','h','cpp','cc','cxx'].includes(ext)) return 'c'
      if (['js','ts','jsx','tsx','java','go','rs'].includes(ext)) return 'clike'
      if (['py'].includes(ext)) return 'clike'
      return 'c'
    },
    chatHeight() { if (this.codeCollapsed) return 100; if (this.leftCollapsed) return 60; return 30 }
  },
  methods: {
    selectFile(node) { if (node.type === 'file') { this.selectedFilePath = node.path } },
    toggleDir(node) { node.expanded = !node.expanded },
    toggleCode() { this.codeCollapsed = !this.codeCollapsed },
    toggleLeft() { this.leftCollapsed = !this.leftCollapsed },
    toggleChatOnly() { this.chatOnly = !this.chatOnly; if (this.chatOnly) { this.leftCollapsed = true; this.codeCollapsed = true } else { this.leftCollapsed = false; this.codeCollapsed = false } },
    onEnter(e) { if (e.shiftKey) return; e.preventDefault(); this.send() },
    triggerUpload() { const el = document.getElementById('file-input'); if (el) el.click() },
    async handleUpload(e) {
      const f = e.target.files && e.target.files[0]
      if (!f) return
      const isZip = /\.zip$/i.test(f.name)
      if (isZip) { this.lastZipFile = null; this.toast('暂不支持项目包上传'); e.target.value = ''; return }
      const reader = new FileReader()
      reader.onload = async () => {
        const text = String(reader.result || '')
        const lines = text.split(/\r?\n/)
        const parsed = lines.map((s) => ({ text: s || '', tags: [] }))
        const path = 'uploaded/' + f.name
        this.codeTextMap[path] = text
        sampleCode[path] = parsed
        let uploadedRoot = this.fileTree.find(n => n.path === 'uploaded')
        if (!uploadedRoot) { uploadedRoot = { id: 'root-uploaded', name: 'uploaded', type: 'dir', path: 'uploaded', expanded: true, children: [] }; this.fileTree.push(uploadedRoot) }
        uploadedRoot.children.push({ id: 'uploaded-' + Date.now(), name: f.name, type: 'file', path })
        this.selectedFilePath = path
        this.codeCollapsed = false
        this.$nextTick(() => Prism.highlightAll())
        await this.analyze(f.name, text)
      }
      reader.readAsText(f)
      e.target.value = ''
    },
    async deleteFile(node) {
      try {
        const uploadedRoot = this.fileTree.find(n => n.path === 'uploaded')
        if (uploadedRoot && uploadedRoot.children) { uploadedRoot.children = uploadedRoot.children.filter(c => c.path !== node.path) }
        delete sampleCode[node.path]
        if (this.selectedFilePath === node.path) { const next = (uploadedRoot && uploadedRoot.children[0]) ? uploadedRoot.children[0].path : 'arm/driver.c'; this.selectedFilePath = next }
        this.$nextTick(() => Prism.highlightAll())
        const base = (this.apiBase || '').replace(/\/+$/,'')
        const fd = new FormData()
        fd.append('userId', 'demo')
        fd.append('codeId', node.name)
        await fetch(base + '/Code/removeCode', { method: 'POST', body: fd }).catch(() => {})
        this.toast('已删除文件')
      } catch (_) { this.toast('删除失败') }
    },
    async downloadReport() {
      const codeId = (this.selectedFilePath || '').split('/').pop() || 'report'
      if (this.reportData) {
        const content = typeof this.reportData === 'string' ? this.reportData : JSON.stringify(this.reportData)
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = codeId + '.report.txt'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
        this.toast('报告下载成功')
        return
      }
      try {
        const base = (this.apiBase || '').replace(/\/+$/,'')
        const fd = new FormData()
        fd.append('userId', 'demo')
        fd.append('codeId', codeId)
        const r = await fetch(base + '/Code/report', { method: 'POST', body: fd })
        if (r && r.ok) {
          const blob = await r.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = codeId + '.report.txt'
          document.body.appendChild(a)
          a.click()
          a.remove()
          URL.revokeObjectURL(url)
          this.toast('报告下载成功')
          return
        }
        this.toast('后端报告生成失败，使用前端备用报告')
        this.backupDownloadReport()
      } catch (_) {
        this.toast('后端报告生成失败，使用前端备用报告')
        this.backupDownloadReport()
      }
    },
    backupDownloadReport() {
      const content = this.reportData ? JSON.stringify(this.reportData) : this.buildReport()
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const base = (this.selectedFilePath || 'report').split('/').pop()
      a.download = base + '.report.txt'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    },
    buildReport() {
      const lines = this.currentCode
      const funcs = lines.filter(l => l.type === 'function')
      const list = funcs.map(l => `${l.fn || 'unknown'} | ${((l.tags||[])[0]) || 'common'}`)
      const s = this.stats
      const conf = this.config
      return [
        `file: ${this.selectedFilePath}`,
        `arch: ${s.fileArch}`,
        `granularity: ${conf.granularity}`,
        `level: ${conf.level}`,
        `targetArch: ${conf.targetArch}`,
        `funcCount: ${s.funcCount}`,
        `riscvFuncCount: ${s.riscvFuncCount}`,
        `functions:`,
        ...list
      ].join('\n')
    },
    async send() {
      if (!this.inputText.trim()) return
      const userMsgId = Date.now() + '-u'
      this.messages.push({ id: userMsgId, role: 'user', text: this.inputText })
      const loadingId = Date.now() + '-loading'
      this.messages.push({ id: loadingId, role: 'system', text: '分析中…' })
      const codeId = (this.selectedFilePath || '').split('/').pop() || 'code.c'
      const text = this.codeTextMap[this.selectedFilePath] || this.currentCode.map(l => l.text).join('\n')
      const ok = await this.analyze(codeId, text)
      const idx = this.messages.findIndex(m => m.id === loadingId)
      if (idx >= 0) {
        const reply = (ok && this.lastReply) ? this.lastReply : `已接收需求，正在分析 ${this.selectedFilePath}`
        this.messages.splice(idx, 1, { id: loadingId + '-done', role: 'system', text: reply })
      }
      this.inputText = ''
      this.$nextTick(() => { const box = document.querySelector('.chat-history'); if (box) box.scrollTop = box.scrollHeight })
    },
    async analyze(codeId, codeText) {
      try {
        const base = (this.apiBase || '').replace(/\/+$/,'')
        const fd = new FormData()
        const ext = (codeId.split('.').pop() || 'c').toLowerCase()
        fd.append('userId', 'demo')
        fd.append('codeId', codeId)
        fd.append('code', codeText || '')
        fd.append('language', ['c','h','cpp','cc','cxx','py','js','ts','java','go','rs'].includes(ext) ? ext : 'c')
        fd.append('prompt', this.inputText || '')
        if (!this.inputText){
          const r = await fetch(base + '/Analysis/analyze', { method: 'POST', body: fd })
          if (!r || !r.ok) { this.toast('后端分析失败，保留未标注预览'); return false }
          const data = await r.json().catch(() => null)
          if (!data || data.state !== 'success' || !data.rst) { this.toast('后端分析失败，保留未标注预览'); return false }
          const { reply, annotations, report, stats } = data.rst
          this.lastReply = reply || ''
          this.applyAnnotations(this.selectedFilePath, annotations || [])
          this.reportData = report || null
          this.serverStats = stats || null
        }
        else{
          const r = await fetch(base + '/Analysis/chat', { method: 'POST', body: fd })
          if (!r || !r.ok) { this.toast('后端分析失败，保留未标注预览'); return false }
          const data = await r.json().catch(() => null)
          if (!data || data.state !== 'success' || !data.rst) { this.toast('后端分析失败，保留未标注预览'); return false }
          this.lastReply = data.rst
          return true
        }
        this.$nextTick(() => Prism.highlightAll())
        this.toast('分析完成，已应用标注与统计')
        return true
      } catch (_) {
        this.toast('后端分析异常，保留未标注预览')
        return false
      }
    },
    applyAnnotations(path, annotations) {
      const lines = sampleCode[path] || []
      annotations.forEach(a => {
        const i = typeof a.line === 'number' ? a.line - 1: (typeof a.index === 'number' ? a.index : -1)
        if (i >= 0 && i < lines.length) {
          const tags = Array.isArray(a.tags) ? a.tags : (a.tag ? [a.tag] : [])
          lines[i] = Object.assign({}, lines[i], { tags, type: a.type, fn: a.fn })
        }
      })
    },
    fontUp() { this.fontSize = Math.min(22, this.fontSize + 1) },
    fontDown() { this.fontSize = Math.max(10, this.fontSize - 1) },
    copyCode() { const text = this.currentCode.map(l => l.text).join('\n'); navigator.clipboard.writeText(text); this.toast('已复制当前代码') },
    lineClass(line) {
      const target = this.config.targetArch
      const showAll = target === 'all'
      const hasArm = (line.tags || []).includes('arm')
      const hasRiscv = (line.tags || []).includes('riscv')
      const gran = this.config.granularity
      const isFunction = line.type === 'function'
      const isBlock = line.type === 'block'
      const isStmt = line.type === 'stmt'
      let match = false
      if (showAll) match = hasArm || hasRiscv || (line.tags || []).includes('common')
      else if (target === 'arm') match = hasArm
      else if (target === 'riscv') match = hasRiscv
      else match = false
      if (!match) return ''
      if (gran === 'file') return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : ''
      if (gran === 'function' && isFunction) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : ''
      if (gran === 'block' && isBlock) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : ''
      if (gran === 'stmt' && isStmt) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : ''
      if (gran === 'mixed') return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : ''
      return ''
    },
    labelClass(line){
      const t = (line.tags||[])[0] || ''
      if (t==='arm') return 'label-arm'
      if (t==='riscv') return 'label-riscv'
      if (t==='common') return 'label-common'
      return 'label-empty'
    },
    lineLabel(line){
      const t = (line.tags||[])[0] || ''
      if (!t) return ''
      return t==='common' ? '通用' : t
    },
    refreshStats(){ this.$nextTick(() => {}) },
    toast(text) { this.toastText = text; this.toastVisible = true; clearTimeout(this._toastTimer); this._toastTimer = setTimeout(() => { this.toastVisible = false }, 1200) },
    toggleTheme() { this.theme = this.theme === 'light' ? 'dark' : 'light'; document.documentElement.setAttribute('data-theme', this.theme); localStorage.setItem('theme', this.theme) }
  },
  mounted() {
    Prism.highlightAll()
    const savedTheme = localStorage.getItem('theme') || 'light'
    this.theme = savedTheme
    document.documentElement.setAttribute('data-theme', savedTheme)
    const savedConfig = JSON.parse(localStorage.getItem('config') || '{}')
    this.config = Object.assign(this.config, savedConfig)
    const savedCollapsed = JSON.parse(localStorage.getItem('collapsed') || '{}')
    this.leftCollapsed = !!savedCollapsed.left
    this.codeCollapsed = !!savedCollapsed.code
    this.chatOnly = !!savedCollapsed.chatOnly
    this.apiBase = localStorage.getItem('apiBase') || this.apiBase
    window.addEventListener('keydown', (e) => { if (e.ctrlKey && e.key === 'Enter') this.send(); if (!e.ctrlKey && e.key.toLowerCase() === 'l') this.toggleLeft(); if (!e.ctrlKey && e.key.toLowerCase() === 'p') this.toggleCode(); if (e.key === 'Escape') this.searchTextRaw = '' })
    this.$watch('searchTextRaw', (val) => { clearTimeout(this._searchTimer); this._searchTimer = setTimeout(() => { this.searchText = val }, 200) })
    this.$watch('leftCollapsed', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.left = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
    this.$watch('codeCollapsed', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.code = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
    this.$watch('chatOnly', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.chatOnly = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
  },
  updated() { Prism.highlightAll() }
}
</script>
