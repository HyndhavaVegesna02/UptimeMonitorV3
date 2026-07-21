import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('boots and redirects "/" to the Dashboard tab by default (STORY-121)', async () => {
    render(<App />)
    expect(
      await screen.findByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
  })
})
