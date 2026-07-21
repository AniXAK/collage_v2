<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

let color = ref('#ffffff')
let border = ref(50)
let orientation = ref('horizontal')
let taskIds = ref([])
let status = ref([])
let processedImages = ref([])
let collageImage = ref(null)

// UI state
let isProcessing = ref(false)
let selectedFiles = ref([]) // To store File objects and their preview URLs
let fileInputRef = ref(null)

const triggerFileInput = () => {
  fileInputRef.value.click()
}

const onFileChange = (event) => {
  const files = event.target.files
  if (!files) return
  
  // Convert FileList to Array and create preview URLs
  const newFiles = Array.from(files).map(file => ({
    file,
    preview: URL.createObjectURL(file)
  }))
  
  selectedFiles.value = [...selectedFiles.value, ...newFiles]
  // Reset input value so same files can be selected again if removed
  event.target.value = ''
}

const removeFile = (index) => {
  const removed = selectedFiles.value.splice(index, 1)[0]
  URL.revokeObjectURL(removed.preview)
}

function downloadCollage() {
  const a = document.createElement('a')
  a.href = collageImage.value
  a.download = 'collage.png'
  a.click()
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) {
    alert('Пожалуйста, выберите хотя бы один файл')
    return
  }
  
  isProcessing.value = true
  processedImages.value = []
  taskIds.value = []
  collageImage.value = null

  let formData = new FormData()
  for (const item of selectedFiles.value) {
    formData.append('image[]', item.file)
  }

  try {
    const { data } = await axios.post('http://127.0.0.1:5000/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    taskIds.value = data.task_ids
    taskIds.value.forEach((id, index) => checkStatus(id, index))
  } catch (error) {
    console.error("Ошибка при загрузке", error)
    isProcessing.value = false
    alert('Произошла ошибка при отправке файлов')
  }
}

const checkStatus = async (taskId, index) => {
  const interval = setInterval(async () => {
    try {
      const { data } = await axios.get(`http://127.0.0.1:5000/status/${taskId}`)
      status.value[index] = data.state

      if (data.state === 'SUCCESS') {
        clearInterval(interval)

        const filename = data.result
        const response = await axios.get(`http://127.0.0.1:5000/download/${filename}`, {
          responseType: 'blob'
        })

        const blobUrl = URL.createObjectURL(response.data)
        processedImages.value.push(blobUrl)
      } else if (data.state === 'FAILURE') {
         clearInterval(interval)
         console.error("Task failed", taskId)
      }
    } catch (e) {
       console.error("Error checking status", e)
       clearInterval(interval)
    }
  }, 2000)
}

// Следим, когда загрузятся все изображения
watch(processedImages, (newVal) => {
  if (newVal.length === taskIds.value.length && newVal.length > 0) {
    buildCollage(newVal)
  }
}, { deep: true })

function buildCollage(urls) {
  let loadedCount = 0
  let loadedImages = []
  const gap = Number(border.value) || 0
  const cellHeight = 1080
  const cellWidth = 1080

  urls.forEach(url => {
    const img = new Image()
    img.onload = () => {
      loadedImages.push(img)
      loadedCount++
      if (loadedCount === urls.length) {
        let totalWidth = gap
        let totalHeight = gap
        
        if (orientation.value === 'horizontal') {
          loadedImages.forEach(im => {
            const aspect = im.width / im.height
            totalWidth += cellHeight * aspect + gap
          })
          totalHeight = cellHeight + gap * 2
        } else {
          loadedImages.forEach(im => {
            const aspect = im.height / im.width
            totalHeight += cellWidth * aspect + gap
          })
          totalWidth = cellWidth + gap * 2
        }

        const canvas = document.createElement('canvas')
        canvas.width = totalWidth
        canvas.height = totalHeight
        const ctx = canvas.getContext('2d')

        ctx.fillStyle = color.value || '#ffffff'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        let x = gap
        let y = gap
        loadedImages.forEach(im => {
          if (orientation.value === 'horizontal') {
            const aspect = im.width / im.height
            const drawWidth = cellHeight * aspect
            ctx.drawImage(im, x, gap, drawWidth, cellHeight)
            x += drawWidth + gap
          } else {
            const aspect = im.height / im.width
            const drawHeight = cellWidth * aspect
            ctx.drawImage(im, gap, y, cellWidth, drawHeight)
            y += drawHeight + gap
          }
        })

        collageImage.value = canvas.toDataURL('image/png')
        isProcessing.value = false
      }
    }
    img.src = url
  })
}
</script>

<template>
  <div class="general_page">
    <div class="glass-panel left_bar">
      <h2 class="title">Создать коллаж</h2>
      
      <div class="dropzone" @click="triggerFileInput">
        <div class="dropzone-content">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          <p>Нажмите для загрузки фото</p>
        </div>
        <input type="file" ref="fileInputRef" multiple @change="onFileChange" accept="image/*" style="display: none;">
      </div>

      <div class="preview-container" v-if="selectedFiles.length > 0">
        <div class="preview-item" v-for="(item, index) in selectedFiles" :key="index">
          <img :src="item.preview" class="preview-img" />
          <button class="remove-btn" @click.stop="removeFile(index)">×</button>
        </div>
      </div>

      <div class="settings-group">
        <div class="input-wrap">
          <label>Ориентация</label>
          <div class="segmented-control">
            <button class="segment" :class="{active: orientation === 'horizontal'}" @click="orientation = 'horizontal'">Горизонтальная</button>
            <button class="segment" :class="{active: orientation === 'vertical'}" @click="orientation = 'vertical'">Вертикальная</button>
          </div>
        </div>

        <div class="input-wrap">
          <label>Цвет фона</label>
          <div class="color-picker-wrap">
            <input type="color" v-model="color" class="color-input">
            <input type="text" v-model="color" class="text-input" placeholder="#ffffff">
          </div>
        </div>
        <div class="input-wrap">
          <label>Отступ (px)</label>
          <input type="number" v-model="border" class="text-input" placeholder="50" min="0" max="500">
        </div>
      </div>

      <button 
        class="submit-btn" 
        @click="uploadFiles" 
        :disabled="selectedFiles.length === 0 || isProcessing"
        :class="{ 'processing': isProcessing }"
      >
        <span v-if="!isProcessing">Сгенерировать</span>
        <span v-else class="loader"></span>
      </button>
    </div>

    <div class="glass-panel right_page">
      <div class="result-area" :class="{'empty': !collageImage, 'loading': isProcessing}">
        
        <div v-if="isProcessing && !collageImage" class="processing-state">
           <div class="spinner"></div>
           <p>Создаем магию...</p>
        </div>

        <div v-else-if="!collageImage && !isProcessing" class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          <p>Здесь появится ваш коллаж</p>
        </div>

        <img v-if="collageImage" :src="collageImage" alt="Коллаж" class="final-collage" />
      </div>

      <div class="action-bar">
        <button class="download-btn" :disabled="!collageImage" @click="downloadCollage">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          Скачать результат
        </button>
      </div>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* {
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
}

html, body {
  padding: 0;
  margin: 0;
  height: 100vh;
  width: 100vw;
  background: #fdfcff;
  display: flex;
  color: #1a1b1f;
  overflow: hidden;
}

.general_page {
  display: flex;
  flex-direction: row;
  width: 100vw;
  height: 100vh;
  gap: 24px;
  padding: 24px;
  max-width: none;
}

.glass-panel {
  background: #f0f4f8;
  border-radius: 32px;
  display: flex;
  flex-direction: column;
}

/* Left Bar */
.left_bar {
  flex: 0 0 450px;
  padding: 40px;
  z-index: 10;
  overflow-y: auto;
  scrollbar-width: none;
}
.left_bar::-webkit-scrollbar {
  display: none;
}

.title {
  margin: 0 0 32px 0;
  font-size: 28px;
  font-weight: 600;
  color: #1a1b1f;
  text-align: left;
}

.dropzone {
  border: 2px dashed #74777f;
  border-radius: 24px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  background: transparent;
  transition: all 0.3s ease;
  margin-bottom: 24px;
}

.dropzone:hover {
  background: rgba(11, 87, 208, 0.08);
  border-color: #0b57d0;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #44474e;
}

.dropzone-content svg {
  color: #0b57d0;
  width: 40px;
  height: 40px;
}

.dropzone-content p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

/* Previews */
.preview-container {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 12px;
  margin-bottom: 24px;
  scrollbar-width: thin;
}

.preview-item {
  position: relative;
  flex: 0 0 70px;
  height: 70px;
  border-radius: 16px;
  overflow: hidden;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ba1a1a;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 0.8;
}

/* Settings */
.settings-group {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 40px;
}

.input-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrap label {
  font-size: 14px;
  font-weight: 600;
  color: #44474e;
  padding-left: 4px;
}

/* Segmented Control */
.segmented-control {
  display: flex;
  background: #e1e2e8;
  border-radius: 100px;
  padding: 4px;
  gap: 4px;
}

.segment {
  flex: 1;
  padding: 12px 16px;
  border-radius: 100px;
  border: none;
  background: transparent;
  color: #44474e;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.segment.active {
  background: #c2e7ff;
  color: #001d35;
}

.color-picker-wrap {
  display: flex;
  gap: 12px;
}

.color-input {
  width: 50px;
  height: 50px;
  padding: 0;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  background: transparent;
  outline: none;
}
.color-input::-webkit-color-swatch-wrapper { padding: 0; }
.color-input::-webkit-color-swatch { border: none; border-radius: 50%; }
.color-input::-moz-color-swatch { border: none; border-radius: 50%; }

.text-input {
  flex: 1;
  width: 100%;
  height: 50px;
  min-height: 50px;
  padding: 0 16px;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 500;
  color: #1a1b1f;
  background: #e1e2e8;
  transition: all 0.2s ease;
  outline: none;
  border-bottom: 2px solid transparent;
  box-sizing: border-box;
}

.text-input:focus {
  border-bottom: 2px solid #0b57d0;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  background: #d3e3fd;
}

/* Hide number input arrows */
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
  -webkit-appearance: none; 
  margin: 0; 
}
input[type=number] {
  -moz-appearance: textfield;
}

/* Submit button */
.submit-btn {
  margin-top: auto;
  height: 56px;
  background: #0b57d0;
  color: white;
  border: none;
  border-radius: 100px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn:hover:not(:disabled) {
  background: #0842a0;
}

.submit-btn:disabled {
  background: #e1e2e8;
  color: #c4c6d0;
  cursor: not-allowed;
}

.loader {
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top: 3px solid white;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* Right Page */
.right_page {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
}

.result-area {
  flex: 1;
  background: #e1e2e8;
  border-radius: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
  position: relative;
  margin-bottom: 24px;
}

.result-area.empty {
  border: 2px dashed #74777f;
  background: transparent;
}

.empty-state, .processing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #74777f;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #c2e7ff;
  border-top: 4px solid #0b57d0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.final-collage {
  max-width: 95%;
  max-height: 95%;
  object-fit: contain;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-radius: 16px;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

.action-bar {
  display: flex;
  justify-content: flex-end;
}

.download-btn {
  height: 48px;
  padding: 0 24px;
  background: #c2e7ff;
  color: #001d35;
  border: none;
  border-radius: 100px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.download-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f8fafc;
}

.download-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>