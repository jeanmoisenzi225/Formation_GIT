// Fixed categorical order — never cycle/reassign per render, always slice from the front.
export const CATEGORICAL = [
  '#2a78d6', // 1 blue
  '#eb6834', // 2 orange
  '#1baf7a', // 3 aqua
  '#eda100', // 4 yellow
  '#e87ba4', // 5 magenta
  '#008300', // 6 green
  '#4a3aa7', // 7 violet
  '#e34948', // 8 red
]

export const STATUS = {
  good: '#0ca30c',
  critical: '#d03b3b',
}

export const CHROME = {
  surface: '#fcfcfb',
  gridline: '#e1e0d9',
  axis: '#c3c2b7',
  textSecondary: '#52514e',
  textMuted: '#898781',
}

export function categoricalColor(index: number): string {
  return CATEGORICAL[index % CATEGORICAL.length]
}
