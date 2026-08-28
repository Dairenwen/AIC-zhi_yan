<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Bell,
  ChevronRight,
  Crown,
  KeyRound,
  LockKeyhole,
  UserRound,
} from 'lucide-vue-next'

import { getData } from '@/api/http'
import PageHeader from '@/components/PageHeader.vue'
import ModelLibraryView from '@/views/ModelLibraryView.vue'
import type { Profile } from '@/types'

const profile = ref<Profile>({
  id: '',
  name: '',
  organization: '',
  role: 'normal_user',
  plan: '科研基础版',
  modelConfigured: false,
})
const route = useRoute()
const activeTab = ref<'profile' | 'model' | 'password' | 'plan'>(route.query.tab === 'model' ? 'model' : 'profile')

onMounted(async () => {
  try {
    profile.value = await getData<Profile>('/users/me')
  } catch {
    // Keep the page usable when profile metadata is temporarily unavailable.
  }
})
</script>

<template>
  <div class="workspace-page profile-page">
    <PageHeader eyebrow="ACCOUNT & MODELS" title="个人中心" description="管理个人资料、安全设置、会员服务和模型连接。">
      <button class="icon-button" type="button" aria-label="通知" title="通知"><Bell :size="17" /></button>
    </PageHeader>

    <div class="profile-layout">
      <aside class="profile-nav">
        <div class="profile-identity">
          <span class="profile-avatar"><UserRound :size="24" /></span>
          <div><strong>{{ profile.name }}</strong><small>{{ profile.organization }}</small></div>
        </div>
        <button :class="{ active: activeTab === 'profile' }" type="button" @click="activeTab = 'profile'"><UserRound :size="16" />个人资料<ChevronRight :size="15" /></button>
        <button :class="{ active: activeTab === 'model' }" type="button" @click="activeTab = 'model'"><KeyRound :size="16" />模型库<ChevronRight :size="15" /></button>
        <button :class="{ active: activeTab === 'password' }" type="button" @click="activeTab = 'password'"><LockKeyhole :size="16" />修改密码<ChevronRight :size="15" /></button>
        <button :class="{ active: activeTab === 'plan' }" type="button" @click="activeTab = 'plan'"><Crown :size="16" />会员服务<ChevronRight :size="15" /></button>
      </aside>

      <section class="profile-panel" :class="{ 'profile-panel--models': activeTab === 'model' }">
        <template v-if="activeTab === 'profile'">
          <div class="panel-heading"><div><h2>个人资料</h2><p>用于工作台展示和任务通知。</p></div></div>
          <div class="form-grid">
            <label><span>用户名称</span><input :value="profile.name" disabled /></label>
            <label><span>所属机构</span><input :value="profile.organization" disabled /></label>
            <label><span>账号角色</span><input :value="profile.role === 'system_admin' ? '系统管理员' : '普通用户'" disabled /></label>
            <label><span>账号 ID</span><input :value="profile.id" disabled /></label>
          </div>
        </template>

        <template v-else-if="activeTab === 'model'">
          <ModelLibraryView embedded />
        </template>

        <template v-else-if="activeTab === 'password'">
          <div class="panel-heading"><div><h2>修改密码</h2><p>更新密码后将退出其他已登录设备。</p></div></div>
          <div class="form-stack">
            <label><span>当前密码</span><input type="password" /></label>
            <label><span>新密码</span><input type="password" /></label>
            <label><span>确认新密码</span><input type="password" /></label>
          </div>
          <div class="form-actions"><button class="primary-button" type="button"><LockKeyhole :size="15" />更新密码</button></div>
        </template>

        <template v-else>
          <div class="panel-heading"><div><h2>会员服务</h2><p>查看当前套餐和本周期科研额度。</p></div><span class="plan-badge">{{ profile.plan }}</span></div>
          <div class="quota-list"><div><span><strong>模型调用</strong><small>本月 1,820 / 5,000 次</small></span><div><i style="width: 36%"></i></div></div><div><span><strong>知识库存储</strong><small>3.2 / 10 GB</small></span><div><i style="width: 32%"></i></div></div></div>
        </template>
      </section>
    </div>
  </div>
</template>
