import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from './Table'

function ExampleTable() {
  return (
    <Table aria-label="Components">
      <TableHead>
        <TableRow>
          <TableHeaderCell>Name</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        <TableRow>
          <TableCell>api-gateway</TableCell>
          <TableCell>Operational</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}

describe('Table', () => {
  it('renders a semantic table (role="table")', () => {
    render(<ExampleTable />)
    expect(screen.getByRole('table', { name: 'Components' })).toBeInTheDocument()
  })

  it('renders header cells as columnheaders with a col scope', () => {
    render(<ExampleTable />)
    const headers = screen.getAllByRole('columnheader')
    expect(headers).toHaveLength(2)
    expect(headers[0]).toHaveTextContent('Name')
    expect(headers[0]).toHaveAttribute('scope', 'col')
    expect(headers[1]).toHaveAttribute('scope', 'col')
  })

  it('renders a data row with the correct number of cells', () => {
    render(<ExampleTable />)
    const rows = screen.getAllByRole('row')
    // header row + one data row
    expect(rows).toHaveLength(2)
    expect(screen.getByText('api-gateway')).toBeInTheDocument()
    expect(screen.getByText('Operational')).toBeInTheDocument()
  })

  it('lets a header cell override its scope (e.g. row headers)', () => {
    render(
      <Table aria-label="Row-scoped">
        <TableBody>
          <TableRow>
            <TableHeaderCell scope="row">Row header</TableHeaderCell>
            <TableCell>value</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    )
    expect(screen.getByRole('rowheader')).toHaveTextContent('Row header')
  })

  it('applies the table surface class for the shared styling', () => {
    const { container } = render(<ExampleTable />)
    expect(container.querySelector('.table')).not.toBeNull()
  })
})
