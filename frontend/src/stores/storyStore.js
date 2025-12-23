import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const useStoryStore = defineStore('story', {
  state: () => ({
    files: [],
    previews: [],
    photos: [],
    panels: [],
    summary: '',
    style: 'Heartwarming (溫馨)',
    language: 'zh-TW',
    loading: {
      analyze: false,
      story: false,
      export: false
    },
    exportLink: '',
    photoPreviewMap: {}
  }),
  actions: {
    setFiles(fileList) {
      this.files = []
      this.photos = []
      this.panels = []
      this.summary = ''
      this.photoPreviewMap = {}
      if (this.previews.length) {
        this.previews.forEach((url) => URL.revokeObjectURL(url))
      }
      this.previews = []
      Array.from(fileList || []).forEach((file) => {
        this.files.push(file)
        this.previews.push(URL.createObjectURL(file))
      })
      this.exportLink = ''
    },
    async analyze() {
      if (!this.files.length) return
      this.loading.analyze = true
      try {
        const formData = new FormData()
        this.files.forEach((file) => formData.append('files', file))
        const { data } = await axios.post(`${API_BASE_URL}/api/analyze`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.photos = data.photos
        const previewMap = {}
        this.photos.forEach((photo, idx) => {
          previewMap[photo.image_id] = this.previews[idx] || ''
        })
        this.photoPreviewMap = previewMap
        this.exportLink = ''
      } catch (error) {
        console.error('Analyze failed', error)
        throw error
      } finally {
        this.loading.analyze = false
      }
    },
    async generateStory() {
      if (!this.photos.length) return
      this.loading.story = true
      try {
        const payload = {
          photos: this.photos.map((photo) => ({
            image_id: photo.image_id,
            analysis: photo.analysis
          })),
          style: this.style,
          language: this.language
        }
        const { data } = await axios.post(`${API_BASE_URL}/api/story`, payload)
        this.panels = data.panels || []
        this.summary = data.summary || ''
        this.exportLink = ''
      } catch (error) {
        console.error('Story generation failed', error)
        throw error
      } finally {
        this.loading.story = false
      }
    },
    async exportStory() {
      if (!this.panels.length) return
      this.loading.export = true
      try {
        const payload = {
          storybook: {
            title: 'AI Story Album',
            panels: this.panels,
            summary: this.summary
          },
          format: 'pdf'
        }
        const { data } = await axios.post(`${API_BASE_URL}/api/export`, payload)
        this.exportLink = `${API_BASE_URL}${data.download_url}`
      } catch (error) {
        console.error('Export failed', error)
        throw error
      } finally {
        this.loading.export = false
      }
    }
  }
})
