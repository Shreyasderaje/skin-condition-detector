// Color + distinct shape + text label, so risk is readable for colorblind users.
const STYLES = {
  LOW: {
    box: 'border-green-400 bg-green-100 text-green-800',
    icon: '●',
  },
  MEDIUM: {
    box: 'border-amber-400 bg-amber-100 text-amber-900',
    icon: '▲',
  },
  HIGH: {
    box: 'border-red-400 bg-red-100 text-red-800',
    icon: '■',
  },
}

export default function RiskBadge({ risk, size = 'md' }) {
  const style = STYLES[risk] || STYLES.LOW
  const sizing =
    size === 'lg' ? 'px-6 py-3 text-3xl' : size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-4 py-2 text-lg'
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-xl border-2 font-bold tracking-wide ${style.box} ${sizing}`}
    >
      <span aria-hidden>{style.icon}</span>
      {risk}
    </span>
  )
}
