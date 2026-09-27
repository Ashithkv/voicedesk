const LABELS = {
  appointment: 'Appointment',
  callback: 'Callback',
  general_information: 'Info',
  unknown: 'Unclear',
}

export default function IntentTag({ intent }) {
  if (!intent) return <span className="intent-tag intent-none">— log —</span>
  return (
    <span className={`intent-tag intent-${intent}`}>
      {LABELS[intent] || intent}
    </span>
  )
}
