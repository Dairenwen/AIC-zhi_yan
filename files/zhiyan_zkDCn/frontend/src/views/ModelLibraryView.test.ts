import { parse } from '@vue/compiler-sfc'
import { describe, expect, it } from 'vitest'

import source from './ModelLibraryView.vue?raw'

describe('ModelLibraryView', () => {
  it('presents the dialogue model library as actionable model cards', () => {
    const { descriptor } = parse(source, { filename: 'ModelLibraryView.vue' })
    const template = descriptor.template?.content || ''

    expect(template).toContain('模型库')
    expect(template).toContain('v-for="item in modelTypes"')
    expect(template).toContain('activeType')
    expect(template).toContain('模型类型')
    expect(template).toContain('平台通用模型')
    expect(template).toContain('添加模型')
    expect(template).toContain('测试')
    expect(template).toContain('编辑')
    expect(template).toContain('设为默认')
    expect(template).toContain('class="model-card-grid"')
  })

  it('loads and updates the account default dialogue model', () => {
    const { descriptor } = parse(source, { filename: 'ModelLibraryView.vue' })
    const script = descriptor.scriptSetup?.content || ''

    expect(script).toContain("value: 'vertical_domain'")
    expect(script).toContain("getData<DefaultModelConfig>('/model-configs/default')")
    expect(script).toContain("http.post<{ data: DefaultModelConfig }>('/model-configs/default'")
  })

  it('supports rendering inside the personal-center panel', () => {
    const { descriptor } = parse(source, { filename: 'ModelLibraryView.vue' })
    const script = descriptor.scriptSetup?.content || ''
    const template = descriptor.template?.content || ''

    expect(script).toContain("defineProps<{ embedded?: boolean }>()")
    expect(template).toContain("'model-library-page--embedded': embedded")
  })
})
