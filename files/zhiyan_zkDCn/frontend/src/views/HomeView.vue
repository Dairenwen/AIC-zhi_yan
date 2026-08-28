<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { CircleHelp, Sun } from 'lucide-vue-next'

import TaskComposer from '@/components/TaskComposer.vue'

const route = useRoute()
const completedMessage = ref('')
const chatMode = ref(false)
const selectedPrompt = ref(typeof route.query.prompt === 'string' ? route.query.prompt : '')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 11) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

function setChatMode(active: boolean) {
  chatMode.value = active
}
</script>

<template>
  <div class="home-view" :class="{ 'home-view--chat-mode': chatMode }">
    <div class="home-topbar">
      <div class="home-actions">
        <button class="text-button" type="button"><CircleHelp :size="15" />使用指南</button>
        <span class="home-action-divider" aria-hidden="true"></span>
        <button class="icon-button" type="button" aria-label="切换显示模式" title="切换显示模式"><Sun :size="18" /></button>
      </div>
    </div>

    <section class="home-hero">
      <div class="home-hero__intro">
        <p class="eyebrow">ZHIYAN RESEARCH WORKSPACE</p>
        <h1>
          <span>{{ greeting }}，</span>
          <span>从问题出发建立你的文献脉络。</span>
        </h1>
        <div class="home-title-rule" aria-hidden="true"><span></span></div>
        <p class="home-subtitle">检索、精读、分析和写作由同一科研工作流持续承接。</p>
      </div>

      <TaskComposer
        :preset="selectedPrompt"
        @chat-mode-change="setChatMode"
        @completed="completedMessage = $event"
      />
      <p v-if="completedMessage" class="completion-note">{{ completedMessage }}</p>
    </section>

    <footer class="home-folio" aria-label="页面信息">
      <span>FOLIO / 001</span>
      <span>EDITORIAL RESEARCH ATELIER</span>
    </footer>
  </div>
</template>
