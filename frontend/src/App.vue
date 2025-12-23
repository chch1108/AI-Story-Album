<script setup>
import { computed } from 'vue'
import { useStoryStore } from './stores/storyStore'

const store = useStoryStore()
const hasFiles = computed(() => store.files.length > 0)
const canGenerateStory = computed(() => store.photos.length > 0)
const canExport = computed(() => store.panels.length > 0)
const storyPanels = computed(() => store.panels || [])

const handleFiles = (event) => {
  const files = event.target.files || []
  store.setFiles(files)
}

const analyzePhoto = async () => {
  try {
    await store.analyze()
  } catch (error) {
    alert('分析失敗，請確認後端服務已啟動。')
    console.error(error)
  }
}

const generateStory = async () => {
  try {
    await store.generateStory()
  } catch (error) {
    alert('故事生成失敗，請檢查 LLM API Key。')
    console.error(error)
  }
}

const exportStory = async () => {
  try {
    await store.exportStory()
  } catch (error) {
    alert('匯出失敗，請稍後再試。')
    console.error(error)
  }
}
</script>

<template>
  <div class="container">
    <header>
      <div>
        <p class="eyebrow">From pixels to prose</p>
        <h1>AI Story Album</h1>
        <p class="subtitle">「每一張照片，都值得被說成一段故事。」</p>
      </div>
    </header>

    <section class="card upload-card">
      <h2>1. 上傳照片</h2>
      <input type="file" accept="image/*" multiple @change="handleFiles" />
      <p class="hint">支援多張 JPG / PNG，本地端處理不外傳。</p>
      <div v-if="store.previews.length" class="preview-grid">
        <div v-for="(preview, idx) in store.previews" :key="idx" class="preview-tile">
          <img :src="preview" :alt="`photo-${idx + 1}`" />
          <span>Photo {{ idx + 1 }}</span>
        </div>
      </div>
      <button :disabled="!hasFiles || store.loading.analyze" @click="analyzePhoto">
        {{ store.loading.analyze ? 'Analyzing…' : 'Analyze Photos' }}
      </button>
    </section>

    <section v-if="store.photos.length" class="card analysis-card">
      <h2>2. 分析摘要</h2>
      <div class="analysis-list">
        <div
          class="analysis-item"
          v-for="(photo, idx) in store.photos"
          :key="photo.image_id"
        >
          <img :src="store.photoPreviewMap[photo.image_id] || store.previews[idx]" alt="analysis thumb" />
          <div class="analysis-text">
            <p class="caption">{{ photo.analysis.caption }}</p>
            <p class="emotion">情緒：{{ photo.analysis.emotion }}</p>
            <p class="tags">色彩：{{ (photo.analysis.color_profile?.dominant_colors || []).join(' / ') }}</p>
            <p class="tags">標籤：{{ (photo.analysis.tags || []).join(' / ') }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="card" :class="{ disabled: !canGenerateStory }">
      <h2>3. 選擇敘事風格</h2>
      <div class="grid">
        <label>
          風格 Style
          <select v-model="store.style">
            <option>Heartwarming (溫馨)</option>
            <option>Humorous (搞笑)</option>
            <option>Poetic / Introspective (文青/詩意)</option>
            <option>Travelogue (旅遊)</option>
            <option>Romantic (浪漫)</option>
            <option>Minimal Documentary</option>
          </select>
        </label>
        <label>
          語言 Language
          <select v-model="store.language">
            <option value="zh-TW">繁體中文</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>
      <button :disabled="!canGenerateStory || store.loading.story" @click="generateStory">
        {{ store.loading.story ? 'Generating…' : 'Create Storybook' }}
      </button>
    </section>

    <section v-if="storyPanels.length" class="card storybook-card">
      <h2>4. 故事書預覽</h2>
      <div class="panel-grid">
        <div
          v-for="panel in storyPanels"
          :key="panel.image_id"
          class="panel-card"
          :style="{ backgroundImage: `linear-gradient(180deg, rgba(5,10,30,0.05) 0%, rgba(5,10,30,0.8) 100%), url(${store.photoPreviewMap[panel.image_id] || ''})` }"
        >
          <div class="panel-overlay">
            <p class="panel-title">{{ panel.title }}</p>
            <p class="panel-body">{{ panel.body }}</p>
          </div>
        </div>
      </div>
      <button :disabled="!canExport || store.loading.export" @click="exportStory">
        {{ store.loading.export ? '匯出中…' : 'Download Storybook (PDF)' }}
      </button>
      <p v-if="store.exportLink" class="hint">
        已準備好：<a :href="store.exportLink" target="_blank" rel="noreferrer">下載 PDF</a>
      </p>
    </section>
  </div>
</template>

<style scoped>
.container {
  max-width: 1040px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 4rem;
}

header {
  margin-bottom: 2.5rem;
}

.eyebrow {
  color: #86a8ff;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-size: 0.75rem;
}

h1 {
  font-size: 2.75rem;
  margin: 0.2rem 0;
  color: #0f172a;
}

.subtitle {
  color: #334155;
  font-size: 1.05rem;
}

.card {
  background: #fff;
  border-radius: 24px;
  padding: 1.75rem;
  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.08);
  margin-bottom: 1.75rem;
}

.upload-card input {
  margin: 0.75rem 0 0.5rem;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
  margin: 1rem 0 0.5rem;
}

.preview-tile {
  background: #f0f6ff;
  border-radius: 18px;
  padding: 0.75rem;
  text-align: center;
  color: #0f172a;
  font-weight: 600;
  font-size: 0.9rem;
}

.preview-tile img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 0.5rem;
}

.analysis-card {
  background: linear-gradient(135deg, #f7fbff, #fff);
}

.analysis-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.analysis-item {
  display: flex;
  gap: 1.25rem;
  background: #fff;
  border-radius: 20px;
  padding: 0.75rem;
  box-shadow: inset 0 0 0 1px rgba(134, 168, 255, 0.2);
}

.analysis-item img {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border-radius: 16px;
}

.analysis-text {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.analysis-text .caption {
  font-weight: 600;
  color: #0f172a;
}

.analysis-text .emotion {
  color: #fb6f24;
  font-weight: 600;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  color: #0f172a;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  margin: 1.25rem 0;
}

.panel-card {
  min-height: 320px;
  border-radius: 24px;
  background-size: cover;
  background-position: center;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  box-shadow: 0 20px 35px rgba(9, 18, 41, 0.2);
}

.panel-overlay {
  padding: 1.5rem;
  color: #fff;
  width: 100%;
}

.panel-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.panel-body {
  line-height: 1.6;
  font-size: 1rem;
}

.hint {
  color: #64748b;
  font-size: 0.9rem;
}

.card.disabled {
  opacity: 0.5;
  pointer-events: none;
}
</style>
