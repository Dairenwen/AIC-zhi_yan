<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Bot,
  CheckCircle2,
  Database,
  ChevronRight,
  FileText,
  Paperclip,
  LoaderCircle,
  Plus,
  Search,
  Send,
  Sparkles,
  UsersRound,
  X,
} from 'lucide-vue-next'

import { getData, http } from '@/api/http'
import { getAgentPromptTemplate } from '@/components/agentPromptTemplates'
import type { CatalogItem, DefaultModelConfig, ModelConfig } from '@/types'

interface RagEvidence {
  evidence_id: string
  chunk_id: string
  document_id: string
  section_path: string
  page_start: number
  page_end: number
  quote: string
}

interface RagDocument {
  document_id: string
  title: string
}

interface RagAnswer {
  status: 'COMPLETED' | 'NO_EVIDENCE' | 'DEGRADED' | 'FAILED'
  answer: string
  evidence: RagEvidence[]
  documents: RagDocument[]
  warnings: string[]
  retrieval: { stages: string[]; candidate_count: number }
  model?: string | null
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  model?: string
  pending?: boolean
  rag?: RagAnswer
}

const emit = defineEmits<{
  completed: [message: string]
  chatModeChange: [active: boolean]
}>()
const props = defineProps<{ preset?: string; projectId?: string; conversationId?: string }>()
const router = useRouter()

const prompt = ref('')
const promptBeforeAgentSelection = ref<string | null>(null)
const model = ref('vertical_domain')
const defaultModelValue = ref('vertical_domain')
const selectedFile = ref<File | null>(null)
const selectedAgent = ref<CatalogItem | null>(null)
const selectedTeam = ref<CatalogItem | null>(null)
const knowledgeBaseMode = ref(false)
const chatMessages = ref<ChatMessage[]>([])
const addMenuOpen = ref(false)
const openSubmenu = ref<'agents' | 'teams' | null>(null)
const agentQuery = ref('')
const agents = ref<CatalogItem[]>([])
const teams = ref<CatalogItem[]>([])
const personalModels = ref<ModelConfig[]>([])
const catalogsLoaded = ref(false)
const menuRoot = ref<HTMLElement | null>(null)
const taskStatus = ref<'idle' | 'submitting' | 'running' | 'completed' | 'error'>('idle')
const taskMessage = ref('')
const progress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)
const promptInput = ref<HTMLTextAreaElement | null>(null)
const chatList = ref<HTMLElement | null>(null)
let thinkingTimer: number | null = null

const canSubmit = computed(() => prompt.value.trim().length > 0 && taskStatus.value !== 'submitting' && taskStatus.value !== 'running')
const selectedResource = computed(() => selectedAgent.value ?? selectedTeam.value)
const filteredAgents = computed(() => {
  const keyword = agentQuery.value.trim().toLowerCase()
  return agents.value.filter((item) => !keyword || `${item.name}${item.description}${item.category ?? ''}`.toLowerCase().includes(keyword))
})
const filteredTeams = computed(() => {
  const keyword = agentQuery.value.trim().toLowerCase()
  return teams.value.filter((item) => !keyword || `${item.name}${item.description}`.toLowerCase().includes(keyword))
})
const isChatMode = computed(() => chatMessages.value.length > 0)

watch(isChatMode, (active) => emit('chatModeChange', active), { immediate: true })
watch(chatMessages, () => {
  void nextTick(() => {
    if (chatList.value) chatList.value.scrollTop = chatList.value.scrollHeight
  })
}, { deep: true })

const fileAccept = computed(() => {
  if (selectedAgent.value?.code === 'paper_reading') return '.pdf,application/pdf'
  if (selectedAgent.value?.code === 'academic_compliance') {
    return '.md,.txt,.docx,.pdf,text/markdown,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf'
  }
  if (selectedAgent.value?.code === 'academic_translation') {
    return '.md,.txt,.docx,.pdf,text/markdown,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf'
  }
  if (selectedAgent.value?.code === 'patent_drafting') {
    return '.md,.markdown,.txt,.docx,.pptx,.ppsx,.pdf,.py,.go,.java,.js,.ts,.tsx,.rs,.c,.h,.cpp,.hpp'
  }
  if (selectedAgent.value?.code === 'academic_figure') {
    return '.csv,.tsv,.xls,.xlsx,.json,.jsonl,.pdf,.docx,.txt,.md,.tex,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff'
  }
  return '.pdf,.doc,.docx,.txt,.md,.csv,.xlsx'
})

function modelDisplayName(value?: string) {
  if (value === 'vertical_domain' || value === 'qwen3.6-dpo' || value === 'platform') return '平台通用模型'
  if (value === 'auto') return '自动选择模型'
  if (value?.startsWith('model_config:')) {
    return personalModels.value.find((item) => `model_config:${item.id}` === value)?.name || '个人模型'
  }
  return value || ''
}

function ragStatusLabel(status: RagAnswer['status']) {
  if (status === 'COMPLETED') return '回答完成'
  if (status === 'NO_EVIDENCE') return '证据不足'
  if (status === 'DEGRADED') return '降级回答'
  return '请求失败'
}

function evidenceDocumentTitle(rag: RagAnswer, evidence: RagEvidence) {
  return rag.documents.find((item) => item.document_id === evidence.document_id)?.title || '未命名文献'
}

function evidencePageLabel(evidence: RagEvidence) {
  return evidence.page_start === evidence.page_end
    ? `第 ${evidence.page_start} 页`
    : `第 ${evidence.page_start}-${evidence.page_end} 页`
}

function ragWarningLabel(warning: string) {
  const labels: Record<string, string> = {
    AUTHORIZED_LIBRARY_EMPTY: '当前账号的授权文献库为空，请先将文献加入收藏夹并完成切片。',
    NO_RELEVANT_AUTHORIZED_CHUNK: '授权文献中未检索到与问题相关的切片。',
    SEMANTIC_RETRIEVAL_DISABLED_LEXICAL_FALLBACK: '语义检索未启用，本次使用关键词检索。',
    SEMANTIC_RETRIEVAL_UNAVAILABLE_LEXICAL_FALLBACK: '语义检索暂不可用，本次已回退到关键词检索。',
    GENERATION_MODEL_AUTHENTICATION_FAILED: '模型服务拒绝鉴权，请检查模型服务端的 API Key 校验配置。',
    GENERATION_MODEL_TIMEOUT: '模型生成超时，系统已自动重试，请稍后再试。',
    GENERATION_MODEL_OUTPUT_INVALID: '模型返回格式不符合知识库引用要求，请重试或更换模型。',
    GENERATION_MODEL_CONNECTION_FAILED: '模型连接在生成阶段失败，系统已自动重试。',
    GENERATION_FAILED_EVIDENCE_PRESERVED: '生成模型暂不可用，以下检索证据仍可核对。',
  }
  return labels[warning] || warning
}

function ragAnswerBlocks(content: string) {
  const blocks: Array<{ heading: string; paragraphs: string[] }> = []
  let current = { heading: '', paragraphs: [] as string[] }
  for (const segment of content.split(/\n\s*\n/).map((item) => item.trim()).filter(Boolean)) {
    const lines = segment.split('\n').map((item) => item.trim()).filter(Boolean)
    const heading = lines[0]?.match(/^##\s+(.+)$/)?.[1]
    if (heading) {
      if (current.heading || current.paragraphs.length) blocks.push(current)
      current = { heading, paragraphs: lines.slice(1) }
    } else {
      current.paragraphs.push(lines.join(' '))
    }
  }
  if (current.heading || current.paragraphs.length) blocks.push(current)
  return blocks
}

watch(() => props.preset, (value) => {
  if (value) prompt.value = value
}, { immediate: true })

watch(() => props.conversationId, async (value) => {
  if (!value) {
    chatMessages.value = []
    return
  }
  try {
    const items = await getData<Array<{ role: 'user' | 'assistant' | 'system'; content: string }>>(`/conversations/${value}/messages`)
    chatMessages.value = items
      .filter((item) => item.role === 'user' || item.role === 'assistant')
      .map((item) => ({ role: item.role as 'user' | 'assistant', content: item.content }))
  } catch {
    chatMessages.value = []
  }
}, { immediate: true })

function chooseFile() {
  closeAddMenu()
  fileInput.value?.click()
}

function onFileChange(event: Event) {
  const files = (event.target as HTMLInputElement).files
  selectedFile.value = files?.[0] ?? null
}

function removeSelectedFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function loadCatalogs() {
  if (catalogsLoaded.value) return
  catalogsLoaded.value = true
  const [agentResult, teamResult] = await Promise.allSettled([
    getData<CatalogItem[]>('/agents'),
    getData<CatalogItem[]>('/agent-teams'),
  ])
  agents.value = agentResult.status === 'fulfilled' ? agentResult.value : []
  teams.value = teamResult.status === 'fulfilled' ? teamResult.value : []
}

function toggleAddMenu() {
  addMenuOpen.value = !addMenuOpen.value
  if (!addMenuOpen.value) closeAddMenu()
}

function closeAddMenu() {
  addMenuOpen.value = false
  openSubmenu.value = null
  agentQuery.value = ''
}

function openCatalog(type: 'agents' | 'teams') {
  openSubmenu.value = type
  void loadCatalogs()
}

function selectAgent(item: CatalogItem) {
  const isSameAgent = selectedAgent.value?.code === item.code
  if (!selectedAgent.value && promptBeforeAgentSelection.value === null) {
    promptBeforeAgentSelection.value = prompt.value
  }
  selectedAgent.value = item
  selectedTeam.value = null
  knowledgeBaseMode.value = false
  if (item.code === 'academic_translation') model.value = 'auto'
  if (!isSameAgent) {
    prompt.value = getAgentPromptTemplate(item.code)
    void nextTick(() => {
      resetPromptInputHeight()
      focusFirstTemplateField()
    })
  }
  closeAddMenu()
}

function focusFirstTemplateField() {
  const textarea = promptInput.value
  if (!textarea) return
  const marker = '【请补充】'
  const start = prompt.value.indexOf(marker)
  textarea.focus()
  if (start >= 0) textarea.setSelectionRange(start, start + marker.length)
}

function selectTeam(item: CatalogItem) {
  restorePromptBeforeAgent()
  selectedTeam.value = item
  selectedAgent.value = null
  knowledgeBaseMode.value = false
  if (model.value.startsWith('model_config:')) model.value = defaultModelValue.value
  closeAddMenu()
}

function clearSelectedResource() {
  restorePromptBeforeAgent()
  selectedAgent.value = null
  selectedTeam.value = null
  if (model.value.startsWith('model_config:')) model.value = defaultModelValue.value
}

function selectKnowledgeBase() {
  restorePromptBeforeAgent()
  selectedAgent.value = null
  selectedTeam.value = null
  knowledgeBaseMode.value = true
  if (model.value === 'auto') model.value = defaultModelValue.value
  closeAddMenu()
  void nextTick(() => promptInput.value?.focus())
}

function clearKnowledgeBaseMode() {
  knowledgeBaseMode.value = false
}

function restorePromptBeforeAgent() {
  if (!selectedAgent.value) return
  prompt.value = promptBeforeAgentSelection.value ?? ''
  promptBeforeAgentSelection.value = null
  void nextTick(resetPromptInputHeight)
}

function resetPromptInputHeight() {
  promptInput.value?.style.removeProperty('height')
}

function onDocumentPointerDown(event: PointerEvent) {
  if (menuRoot.value && !menuRoot.value.contains(event.target as Node)) closeAddMenu()
}

function onDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeAddMenu()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  void loadPersonalModels()
})

async function loadPersonalModels() {
  try {
    const [items, defaultModel] = await Promise.all([
      getData<ModelConfig[]>('/model-configs'),
      getData<DefaultModelConfig>('/model-configs/default'),
    ])
    personalModels.value = items.filter((item) => item.status === 'ACTIVE')
    defaultModelValue.value = defaultModel.value
    model.value = defaultModel.value
  } catch {
    personalModels.value = []
    defaultModelValue.value = 'vertical_domain'
    model.value = 'vertical_domain'
  }
}

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  stopThinkingPreview()
})

function startThinkingPreview(messageIndex: number) {
  stopThinkingPreview()
  const steps = [
    '正在理解你的问题',
    '正在选择合适的回答角度',
    '正在组织科研语境下的回答',
    '正在检查表达是否清晰',
  ]
  let stepIndex = 0
  thinkingTimer = window.setInterval(() => {
    stepIndex = Math.min(stepIndex + 1, steps.length - 1)
    updateChatMessage(messageIndex, { content: steps[stepIndex] })
  }, 1100)
}

function stopThinkingPreview() {
  if (thinkingTimer == null) return
  window.clearInterval(thinkingTimer)
  thinkingTimer = null
}

function updateChatMessage(index: number, updates: Partial<ChatMessage>) {
  chatMessages.value = chatMessages.value.map((message, messageIndex) => (
    messageIndex === index ? { ...message, ...updates } : message
  ))
}

async function submitChatMessage() {
  const content = prompt.value.trim()
  taskStatus.value = 'submitting'
  taskMessage.value = ''
  progress.value = 5
  const history = chatMessages.value.map((item) => ({ role: item.role, content: item.content }))
  chatMessages.value.push({ role: 'user', content })
  const assistantIndex = chatMessages.value.length
  chatMessages.value.push({
    role: 'assistant',
    content: '正在理解你的问题',
    model: modelDisplayName(model.value),
    pending: true,
  })
  startThinkingPreview(assistantIndex)
  prompt.value = ''

  try {
    const response = await http.post('/chat', {
      prompt: content,
      model: model.value,
      model_config_id: model.value.startsWith('model_config:') ? model.value.slice('model_config:'.length) : null,
      messages: history,
      project_id: props.projectId || null,
      conversation_id: props.conversationId || null,
    })
    const data = response.data.data as { content: string; model?: string }
    stopThinkingPreview()
    updateChatMessage(assistantIndex, {
      content: data.content || '模型没有返回内容，请稍后重试。',
      model: data.model || modelDisplayName(model.value),
      pending: false,
    })
    taskStatus.value = 'idle'
    taskMessage.value = ''
    progress.value = 0
  } catch {
    stopThinkingPreview()
    updateChatMessage(assistantIndex, {
      content: '模型服务暂时不可用，请检查平台通用模型服务。',
      pending: false,
    })
    taskStatus.value = 'error'
    taskMessage.value = ''
  }
}

async function submitRagQuestion() {
  const content = prompt.value.trim()
  taskStatus.value = 'submitting'
  taskMessage.value = ''
  progress.value = 10
  chatMessages.value.push({ role: 'user', content, model: '知识库问答' })
  const assistantIndex = chatMessages.value.length
  chatMessages.value.push({
    role: 'assistant',
    content: '正在检索授权文献与证据',
    model: '个人学术 RAG',
    pending: true,
  })
  prompt.value = ''

  try {
    const response = await http.post<{ data: RagAnswer }>('/rag/answers', {
      question: content,
      document_ids: [],
      stream: false,
      model: model.value,
    }, { timeout: 120000 })
    const data = response.data.data
    updateChatMessage(assistantIndex, {
      content: data.answer,
      model: data.model || modelDisplayName(model.value),
      pending: false,
      rag: data,
    })
    taskStatus.value = 'idle'
    taskMessage.value = ''
    progress.value = 0
  } catch (error) {
    updateChatMessage(assistantIndex, {
      content: requestError(error),
      model: '个人学术 RAG',
      pending: false,
    })
    taskStatus.value = 'error'
    taskMessage.value = ''
  }
}

async function submitTask() {
  if (!canSubmit.value) return
  if (knowledgeBaseMode.value) {
    await submitRagQuestion()
    return
  }
  if (!selectedAgent.value && !selectedTeam.value) {
    await submitChatMessage()
    return
  }

  taskStatus.value = 'submitting'
  taskMessage.value = '正在创建任务'
  progress.value = 5

  try {
    if (selectedTeam.value) {
      const response = await http.post(`/agent-teams/${selectedTeam.value.id}/runs`, {
        prompt: prompt.value.trim(),
        model: model.value,
      })
      const task = response.data.data as { id: string }
      await router.push({ path: '/teams', query: { task: task.id } })
      return
    }
    const agentCode = selectedAgent.value?.code || null
    const requestModel = agentCode === 'academic_translation' ? 'auto' : agentCode === 'arxiv_daily' ? 'source' : model.value
    let attachmentId: string | null = null
    let figureFile: { upload_id: string; file_name: string; kind: 'data' | 'context' | 'sketch' } | null = null
    if (agentCode === 'paper_reading' || agentCode === 'academic_compliance' || agentCode === 'academic_translation' || (agentCode === 'patent_drafting' && selectedFile.value) || (agentCode === 'academic_figure' && selectedFile.value)) {
      if (!selectedFile.value) {
        const message = agentCode === 'paper_reading'
          ? '论文精读需要先上传 PDF 文件'
          : agentCode === 'academic_translation'
            ? '学术翻译需要先上传待翻译文档'
            : '学术合规检测需要先上传论文稿件'
        throw new Error(message)
      }
      const suffix = selectedFile.value.name.toLowerCase().match(/\.[^.]+$/)?.[0] || ''
      if (agentCode === 'paper_reading' && suffix !== '.pdf') {
        throw new Error('论文精读仅支持 PDF 文件')
      }
      if (agentCode === 'academic_compliance' && !['.md', '.txt', '.docx', '.pdf'].includes(suffix)) {
        throw new Error('学术合规检测仅支持 MD、TXT、DOCX 和 PDF 文件')
      }
      if (agentCode === 'academic_translation' && !['.md', '.txt', '.docx', '.pdf'].includes(suffix)) {
        throw new Error('学术翻译仅支持 MD、TXT、DOCX 和 PDF 文件')
      }
      if (agentCode === 'patent_drafting' && !['.md', '.markdown', '.txt', '.docx', '.pptx', '.ppsx', '.pdf', '.py', '.go', '.java', '.js', '.ts', '.tsx', '.rs', '.c', '.h', '.cpp', '.hpp'].includes(suffix)) {
        throw new Error('专利技术材料格式不受支持')
      }
      const figureDataSuffixes = ['.csv', '.tsv', '.xls', '.xlsx', '.json', '.jsonl']
      const figureSketchSuffixes = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff']
      const figureContextSuffixes = ['.pdf', '.docx', '.txt', '.md', '.tex']
      if (agentCode === 'academic_figure' && ![...figureDataSuffixes, ...figureSketchSuffixes, ...figureContextSuffixes].includes(suffix)) {
        throw new Error('绘图输入文件格式不受支持')
      }
      const figureKind = figureDataSuffixes.includes(suffix) ? 'data' : figureSketchSuffixes.includes(suffix) ? 'sketch' : 'context'
      taskMessage.value = agentCode === 'paper_reading' ? '正在上传 PDF' : agentCode === 'patent_drafting' ? '正在上传技术材料' : agentCode === 'academic_figure' ? '正在上传绘图输入' : '正在上传学术文档'
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      if (agentCode === 'academic_figure') formData.append('kind', figureKind)
      const uploadPath = agentCode === 'paper_reading'
        ? '/uploads/papers'
        : agentCode === 'academic_translation'
          ? '/uploads/translations'
          : agentCode === 'patent_drafting'
            ? '/uploads/patents'
            : agentCode === 'academic_figure'
              ? '/uploads/figures'
            : '/uploads/manuscripts'
      const upload = await http.post<{ data: { uploadId: string; fileName?: string; kind?: 'data' | 'context' | 'sketch' } }>(uploadPath, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      attachmentId = upload.data.data.uploadId
      if (agentCode === 'academic_figure') {
        figureFile = {
          upload_id: upload.data.data.uploadId,
          file_name: upload.data.data.fileName || selectedFile.value.name,
          kind: upload.data.data.kind || figureKind,
        }
      }
    }

    taskMessage.value = '正在创建任务'
    const response = await http.post('/tasks', {
      prompt: prompt.value.trim(),
      model: requestModel,
      model_config_id: requestModel.startsWith('model_config:') ? requestModel.slice('model_config:'.length) : null,
      attachment: selectedFile.value?.name || null,
      attachment_id: attachmentId,
      agent_code: agentCode,
      agent_id: selectedAgent.value?.id || null,
      project_id: props.projectId || null,
      conversation_id: props.conversationId || null,
      translation_source_lang: agentCode === 'academic_translation' ? 'en' : null,
      translation_target_lang: agentCode === 'academic_translation' ? 'zh' : null,
      translation_precision: agentCode === 'academic_translation' ? 'reading' : null,
      patent_title: agentCode === 'patent_drafting' ? prompt.value.trim().slice(0, 120) : null,
      patent_workflow_mode: agentCode === 'patent_drafting' ? 'flow_first' : null,
      figure_type: agentCode === 'academic_figure' ? 'auto' : null,
      figure_planning_mode: agentCode === 'academic_figure' ? 'online' : null,
      figure_export_formats: agentCode === 'academic_figure' ? ['png', 'svg', 'pdf'] : null,
      figure_code_formats: agentCode === 'academic_figure' ? ['python', 'r', 'latex', 'mermaid'] : null,
      figure_languages: agentCode === 'academic_figure' ? ['zh', 'en'] : null,
      figure_files: figureFile ? [figureFile] : null,
      arxiv_category: agentCode === 'arxiv_daily' ? 'cs.AI' : null,
      arxiv_refresh: agentCode === 'arxiv_daily' ? false : null,
    })
    const task = response.data.data as { id: string }
    if (selectedAgent.value?.route) {
      await router.push({ path: selectedAgent.value.route, query: { task: task.id, project: props.projectId || undefined } })
      return
    }
    taskStatus.value = 'running'

    const source = new EventSource(`${http.defaults.baseURL}/tasks/${task.id}/events`)
    source.onmessage = (event) => {
      const data = JSON.parse(event.data) as { progress: number; message: string }
      progress.value = data.progress
      taskMessage.value = data.message
    }
    ;['task.started', 'task.progress', 'task.completed'].forEach((eventName) => {
      source.addEventListener(eventName, (event) => {
        const data = JSON.parse((event as MessageEvent).data) as { progress: number; message: string }
        progress.value = data.progress
        taskMessage.value = data.message
        if (eventName === 'task.completed') {
          taskStatus.value = 'completed'
          source.close()
          emit('completed', data.message)
        }
      })
    })
    source.onerror = () => {
      source.close()
      if (taskStatus.value !== 'completed') {
        taskStatus.value = 'error'
        taskMessage.value = '进度连接已断开，请稍后重试'
      }
    }
  } catch (error) {
    taskStatus.value = 'error'
    taskMessage.value = requestError(error)
  }
}

function requestError(error: unknown) {
  const value = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
  return value.response?.data?.error?.message || value.message || '任务创建失败，请稍后重试'
}
</script>

<template>
  <section class="composer" :class="{ 'composer--chat-mode': isChatMode }" aria-label="新建科研任务">
    <div v-if="chatMessages.length" ref="chatList" class="composer-chat" aria-live="polite">
      <article
        v-for="(message, index) in chatMessages"
        :key="`${message.role}-${index}`"
        class="composer-chat__message"
        :class="[`composer-chat__message--${message.role}`, { 'composer-chat__message--pending': message.pending }]"
      >
        <span class="composer-chat__avatar">{{ message.role === 'user' ? '我' : '智研' }}</span>
        <div class="composer-chat__body">
          <div v-if="message.rag" class="rag-answer-content">
            <section v-for="(block, blockIndex) in ragAnswerBlocks(message.content)" :key="blockIndex">
              <h3 v-if="block.heading">{{ block.heading }}</h3>
              <p v-for="(paragraph, paragraphIndex) in block.paragraphs" :key="paragraphIndex">{{ paragraph }}</p>
            </section>
          </div>
          <p v-else>{{ message.content }}</p>
          <details v-if="message.rag" class="rag-answer-details" :open="message.rag.evidence.length > 0">
            <summary class="rag-answer-summary">
              <span
                class="rag-answer-status"
                :class="`rag-answer-status--${message.rag.status.toLowerCase()}`"
              >{{ ragStatusLabel(message.rag.status) }}</span>
              <span>{{ message.rag.evidence.length }} 条证据 · {{ message.rag.documents.length }} 篇文献</span>
            </summary>
            <div v-if="message.rag.evidence.length" class="rag-evidence-list">
              <article v-for="(evidence, evidenceIndex) in message.rag.evidence" :key="evidence.evidence_id" class="rag-evidence-item">
                <div class="rag-evidence-item__header">
                  <span class="rag-evidence-index">[{{ evidenceIndex + 1 }}]</span>
                  <strong class="rag-evidence-title">{{ evidenceDocumentTitle(message.rag, evidence) }}</strong>
                  <span class="rag-evidence-page">{{ evidencePageLabel(evidence) }}</span>
                </div>
                <span class="rag-evidence-section">{{ evidence.section_path || '正文' }}</span>
                <blockquote>{{ evidence.quote }}</blockquote>
              </article>
            </div>
            <p v-for="warning in message.rag.warnings" :key="warning" class="rag-answer-warning">{{ ragWarningLabel(warning) }}</p>
          </details>
          <footer v-if="message.role === 'assistant' && !message.pending" class="composer-chat__meta">
            <small v-if="message.model" class="composer-chat__model">{{ message.model }}</small>
            <small class="composer-chat__disclaimer">内容由智研ai生成</small>
          </footer>
          <small v-else-if="message.model" class="composer-chat__model">{{ message.model }}</small>
        </div>
      </article>
    </div>

    <div class="composer-input-panel">
      <textarea
        ref="promptInput"
        v-model="prompt"
        :rows="selectedAgent ? 8 : 4"
        :placeholder="knowledgeBaseMode ? '基于知识库中的文献提出问题...' : '提出你的研究问题、上传论文，或描述需要完成的科研任务...'"
        aria-label="科研任务内容"
        @keydown.ctrl.enter.prevent="submitTask"
        @keydown.meta.enter.prevent="submitTask"
      ></textarea>

      <div v-if="selectedFile" class="selected-file">
        <FileText :size="14" />
        <span>{{ selectedFile.name }}</span>
        <button type="button" aria-label="移除文件" title="移除文件" @click="removeSelectedFile"><X :size="13" /></button>
      </div>

      <div ref="menuRoot" class="composer__footer">
        <div class="composer__tools">
          <input
            ref="fileInput"
            class="sr-only"
            type="file"
            :accept="fileAccept"
            @change="onFileChange"
          />
          <button
            class="icon-button composer-add-button"
            :class="{ 'composer-add-button--active': addMenuOpen }"
            type="button"
            aria-label="添加内容"
            :aria-expanded="addMenuOpen"
            aria-haspopup="menu"
            title="添加内容"
            @click="toggleAddMenu"
          >
            <Plus :size="17" />
          </button>
          <div v-if="addMenuOpen" class="composer-add-menu" role="menu" aria-label="添加内容">
            <button class="composer-add-menu__item" type="button" role="menuitem" @click="selectKnowledgeBase">
              <Database :size="18" />
              <span>知识库问答</span>
            </button>

            <div class="composer-add-menu__group">
              <button
                class="composer-add-menu__item"
                :class="{ 'composer-add-menu__item--active': openSubmenu === 'agents' }"
                type="button"
                role="menuitem"
                aria-haspopup="menu"
                :aria-expanded="openSubmenu === 'agents'"
                @mouseenter="openCatalog('agents')"
                @click="openCatalog('agents')"
              >
                <Bot :size="18" />
                <span>智能体</span>
                <ChevronRight class="composer-add-menu__chevron" :size="16" />
              </button>
              <div v-if="openSubmenu === 'agents'" class="composer-add-submenu" role="menu" aria-label="选择智能体">
                <label class="composer-add-search">
                  <Search :size="16" />
                  <input v-model="agentQuery" type="search" placeholder="搜索 Agent" aria-label="搜索智能体" />
                </label>
                <div class="composer-add-list">
                  <button v-for="item in filteredAgents" :key="item.id" class="composer-add-option" type="button" role="menuitem" @click="selectAgent(item)">
                    <span class="composer-add-option__icon"><Bot :size="16" /></span>
                    <span class="composer-add-option__copy"><strong>{{ item.name }}</strong><small>{{ item.description }}</small></span>
                  </button>
                  <p v-if="filteredAgents.length === 0" class="composer-add-empty">未找到匹配的智能体</p>
                </div>
              </div>
            </div>

            <div class="composer-add-menu__group">
              <button
                class="composer-add-menu__item"
                :class="{ 'composer-add-menu__item--active': openSubmenu === 'teams' }"
                type="button"
                role="menuitem"
                aria-haspopup="menu"
                :aria-expanded="openSubmenu === 'teams'"
                @mouseenter="openCatalog('teams')"
                @click="openCatalog('teams')"
              >
                <UsersRound :size="18" />
                <span>智囊团</span>
                <ChevronRight class="composer-add-menu__chevron" :size="16" />
              </button>
              <div v-if="openSubmenu === 'teams'" class="composer-add-submenu" role="menu" aria-label="选择智囊团">
                <label class="composer-add-search">
                  <Search :size="16" />
                  <input v-model="agentQuery" type="search" placeholder="搜索智囊团" aria-label="搜索智囊团" />
                </label>
                <div class="composer-add-list">
                  <button v-for="item in filteredTeams" :key="item.id" class="composer-add-option" type="button" role="menuitem" @click="selectTeam(item)">
                    <span class="composer-add-option__icon"><UsersRound :size="16" /></span>
                    <span class="composer-add-option__copy"><strong>{{ item.name }}</strong><small>{{ item.description }}</small></span>
                  </button>
                  <p v-if="filteredTeams.length === 0" class="composer-add-empty">未找到匹配的智囊团</p>
                </div>
              </div>
            </div>
          </div>

          <div v-if="knowledgeBaseMode" class="selected-resource selected-resource--knowledge">
            <span class="selected-resource__icon"><Database :size="14" /></span>
            <span class="selected-resource__name">知识库问答</span>
            <button type="button" aria-label="退出知识库问答" title="退出知识库问答" @click="clearKnowledgeBaseMode"><X :size="13" /></button>
          </div>
          <div v-if="selectedResource" class="selected-resource">
            <span class="selected-resource__icon"><Bot v-if="selectedAgent" :size="14" /><UsersRound v-else :size="14" /></span>
            <span class="selected-resource__name">{{ selectedResource.name }}</span>
            <button type="button" aria-label="移除已选内容" title="移除已选内容" @click="clearSelectedResource"><X :size="13" /></button>
          </div>
          <button
            class="icon-button composer-file-button"
            :class="{ 'composer-file-button--active': selectedFile }"
            type="button"
            aria-label="添加文件"
            title="添加文件"
            @click="chooseFile"
          >
            <Paperclip :size="18" style="transform: rotate(-45deg)" />
          </button>
          <span v-if="selectedAgent?.code === 'academic_translation'" class="composer-fixed-model">translategemma:12b</span>
          <span v-else-if="selectedAgent?.code === 'arxiv_daily'" class="composer-fixed-model">arXivDaily 实时源</span>
          <select v-else v-model="model" class="composer-model-select" aria-label="选择模型">
            <option value="vertical_domain">平台通用模型</option>
            <optgroup v-if="personalModels.length" label="我的模型">
              <option v-for="item in personalModels" :key="item.id" :value="`model_config:${item.id}`">{{ item.name }}</option>
            </optgroup>
          </select>
        </div>
        <button class="send-button" type="button" :disabled="!canSubmit" aria-label="发送任务" title="发送任务" @click="submitTask">
          <LoaderCircle v-if="taskStatus === 'submitting' || taskStatus === 'running'" class="spin" :size="17" />
          <Send v-else :size="17" />
        </button>
      </div>

      <div v-if="taskStatus !== 'idle' && !isChatMode" class="task-feedback" :class="`task-feedback--${taskStatus}`">
        <CheckCircle2 v-if="taskStatus === 'completed'" :size="15" />
        <Sparkles v-else :size="15" />
        <span>{{ taskMessage }}</span>
        <div class="progress-track" aria-hidden="true"><span :style="{ width: `${progress}%` }"></span></div>
      </div>
    </div>
  </section>
</template>
