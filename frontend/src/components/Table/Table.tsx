import type {
  HTMLAttributes,
  TdHTMLAttributes,
  ThHTMLAttributes,
} from 'react'
import { cx } from '../../lib/cx'
import './Table.css'

/**
 * Shared table primitive (STORY-055 AC5) — extracts the `th`/`td`/hairline/
 * uppercase-caption styling that was copy-pasted across the six page CSS
 * files (Dashboard/Availability/Approvals/Check History/Maintenance/
 * Publications) into ONE token-driven place. Deliberately a set of thin
 * semantic wrappers (not a data-driven grid component) so each page keeps
 * full control of its column shape, expandable rows, etc. — only the visual
 * treatment is centralized. `TableHeaderCell` defaults to `scope="col"` so
 * pages keep the `<th scope="col">` semantics their existing role-based
 * tests assert.
 */

export type TableProps = HTMLAttributes<HTMLTableElement>

/** Wrapped in its own horizontally-scrollable `.table-wrapper` (STORY-096
 * AC4) — a wide table (long timestamps, many columns) scrolls WITHIN this
 * container, never forcing the page itself to scroll horizontally. */
export function Table({ className, ...rest }: TableProps) {
  return (
    <div className="table-wrapper">
      <table className={cx('table', className)} {...rest} />
    </div>
  )
}

export type TableHeadProps = HTMLAttributes<HTMLTableSectionElement>

export function TableHead({ className, ...rest }: TableHeadProps) {
  return <thead className={cx('table__head', className)} {...rest} />
}

export type TableBodyProps = HTMLAttributes<HTMLTableSectionElement>

export function TableBody({ className, ...rest }: TableBodyProps) {
  return <tbody className={cx('table__body', className)} {...rest} />
}

export type TableRowProps = HTMLAttributes<HTMLTableRowElement>

export function TableRow({ className, ...rest }: TableRowProps) {
  return <tr className={cx('table__row', className)} {...rest} />
}

export type TableHeaderCellProps = ThHTMLAttributes<HTMLTableCellElement>

export function TableHeaderCell({
  className,
  scope = 'col',
  ...rest
}: TableHeaderCellProps) {
  return (
    <th scope={scope} className={cx('table__header-cell', className)} {...rest} />
  )
}

export type TableCellProps = TdHTMLAttributes<HTMLTableCellElement>

export function TableCell({ className, ...rest }: TableCellProps) {
  return <td className={cx('table__cell', className)} {...rest} />
}
