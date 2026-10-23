import { Shell, useRoute } from './components/Shell'
import { Overview } from './pages/Overview'
import { Workspace } from './pages/Workspace'
import { Registration } from './pages/Registration'
import { Lab } from './pages/Lab'
import { Evidence } from './pages/Evidence'
import { Reports } from './pages/Reports'
import { Settings } from './pages/Settings'

export function App() {
  const [route, go] = useRoute()
  const page = { overview: <Overview go={go} />, workspace: <Workspace go={go} />, registration: <Registration go={go} />, lab: <Lab go={go} />, evidence: <Evidence go={go} />, reports: <Reports go={go} />, settings: <Settings /> }[route]
  return <Shell route={route} go={go}>{page}</Shell>
}
