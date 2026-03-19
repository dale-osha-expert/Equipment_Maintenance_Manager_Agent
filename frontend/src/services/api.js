import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
})

export const uploadXlsx = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload-xlsx', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const importSheets = (sheetUrl) =>
  api.post('/import-sheets', { sheet_url: sheetUrl }).then(r => r.data)

export const processEquipment = (equipment) =>
  api.post('/process', { equipment }).then(r => r.data)

export const exportXlsx = async (equipment) => {
  const response = await api.post('/export-xlsx', { equipment }, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'maintenance_schedule.xlsx')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

