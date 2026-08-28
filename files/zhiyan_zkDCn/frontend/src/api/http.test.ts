import { describe, expect, it } from 'vitest'

import { projectContextFromSearch } from './http'

describe('projectContextFromSearch', () => {
  it('keeps project ownership when opening an Agent workspace', () => {
    expect(projectContextFromSearch('?task=task-1&project=project-42')).toBe('project-42')
  })

  it('returns null outside a project workspace', () => {
    expect(projectContextFromSearch('?task=task-1')).toBeNull()
    expect(projectContextFromSearch('?project=')).toBeNull()
  })
})
