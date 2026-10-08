import {
  BatteryFullIcon,
  CameraIcon,
  CpuIcon,
  DeviceMobileIcon,
  EarIcon,
  HeadphonesIcon,
  LightningIcon,
  MicrophoneIcon,
  MonitorIcon,
  PaletteIcon,
  PersonSimpleRunIcon,
  SparkleIcon,
  SpeakerHighIcon,
  WaveformIcon,
  type Icon,
} from "@phosphor-icons/react"

// Icons for features we know; any other feature (they come from the question) gets a neutral one.
const ICONS: Record<string, Icon> = {
  camera: CameraIcon,
  battery: BatteryFullIcon,
  performance: CpuIcon,
  display: MonitorIcon,
  screen: MonitorIcon,
  charging: LightningIcon,
  design: PaletteIcon,
  software: DeviceMobileIcon,
  sound: SpeakerHighIcon,
  bass: WaveformIcon,
  mic: MicrophoneIcon,
  calls: MicrophoneIcon,
  fit: EarIcon,
  comfort: EarIcon,
  gym: PersonSimpleRunIcon,
  "noise cancellation": HeadphonesIcon,
  anc: HeadphonesIcon,
}

export function areaMeta(
  key: string,
  name?: string
): { name: string; icon: Icon; praise: string } {
  const label = name ?? key.charAt(0).toUpperCase() + key.slice(1)
  return {
    name: label,
    icon: ICONS[key] ?? SparkleIcon,
    praise: `praise its ${label.toLowerCase()}`,
  }
}
