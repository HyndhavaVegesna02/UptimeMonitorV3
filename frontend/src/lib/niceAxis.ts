export interface NiceAxis {
  /** The axis maximum, always >= the input `maxValue` (STORY-139 AC2). */
  niceMax: number
  /** The evenly-spaced step between ticks, itself a "nice" round number
   * (a 1 / 2 / 2.5 / 5 x 10^n multiple). */
  step: number
  /** `tickCount` values from 0 (the reserved baseline, STORY-139 AC1) up to
   * `niceMax` in equal `step` increments. */
  ticks: number[]
}

/**
 * Rounds `value` UP to the nearest "nice" number — a 1 / 2 / 2.5 / 5 x 10^n
 * multiple (the classic Heckpert-style nice-number set, extended with 2.5
 * per the ui-ux-pro-max chart-axis guidance). Ceiling, never nearest: the
 * result is always >= `value` so an axis built from it never clips data.
 */
function niceNumberCeil(value: number): number {
  if (value <= 0) {
    return 0
  }
  const exponent = Math.floor(Math.log10(value))
  const fraction = value / 10 ** exponent
  let niceFraction: number
  if (fraction <= 1) {
    niceFraction = 1
  } else if (fraction <= 2) {
    niceFraction = 2
  } else if (fraction <= 2.5) {
    niceFraction = 2.5
  } else if (fraction <= 5) {
    niceFraction = 5
  } else {
    niceFraction = 10
  }
  return niceFraction * 10 ** exponent
}

/**
 * Derives a 0-baseline "nice" axis (STORY-139 — the response-time chart Y-
 * axis previously ran data-min to data-max with raw, non-round tick values;
 * both defects are fixed here). Given the data's real maximum and a desired
 * tick count, this computes a rounded step so `tickCount - 1` equal
 * increments from 0 comfortably cover `maxValue` — never the data minimum,
 * never a raw fractional tick value. Pure and SVG-agnostic: the chart
 * component only consumes `ticks`/`niceMax`, it never recomputes them.
 */
export function computeNiceAxis(maxValue: number, tickCount: number): NiceAxis {
  if (maxValue <= 0 || tickCount < 2) {
    return { niceMax: 0, step: 0, ticks: Array.from({ length: Math.max(tickCount, 0) }, () => 0) }
  }

  const idealStep = maxValue / (tickCount - 1)
  const step = niceNumberCeil(idealStep)
  const niceMax = step * (tickCount - 1)
  const ticks = Array.from({ length: tickCount }, (_, index) => step * index)

  return { niceMax, step, ticks }
}
