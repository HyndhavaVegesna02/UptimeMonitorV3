import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('boots and renders the /styleguide gallery as the default route', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: 'Design system', level: 1 }),
    ).toBeInTheDocument()
  })
})
