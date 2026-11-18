
import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/api/machines/'

const navigation = [
  { group: 'MAIN MENU', items: [
    { id: 'overview', icon: '▦', label: 'Overview' },
    { id: 'machines', icon: '▤', label: 'Machines' },
  ]},
  { group: 'OPERATIONS', items: [
    { id: 'water', icon: '◉', label: 'Water Options' },
    { id: 'containers', icon: '▱', label: 'Container Types' },
    { id: 'inventory', icon: '▥', label: 'Inventory & Stock' },
  ]},
  { group: 'BUSINESS', items: [
    { id: 'orders', icon: '▣', label: 'Orders' },
    { id: 'payments', icon: '↔', label: 'Payments' },
    { id: 'analytics', icon: '▥', label: 'Analytics' },
  ]},
  { group: 'SYSTEM', items: [
    { id: 'settings', icon: '⚙', label: 'Settings' },
  ]},
]

const sectionInfo = {
  water: {
    title: 'Water Options',
    description: 'Manage water types and availability at vending machines.',
    columns: ['Water option', 'Price', 'Availability'],
  },
  containers: {
    title: 'Container Types',
    description: 'Manage container sizes, fees and availability.',
    columns: ['Container', 'Volume', 'Fee', 'Availability'],
  },
  inventory: {
    title: 'Inventory & Stock',
    description: 'Monitor container stock at each machine location.',
    columns: ['Machine', 'Container type', 'Available quantity', 'Status'],
  },
  orders: {
    title: 'Orders',
    description: 'Review customer orders across your machine network.',
    columns: ['Order ID', 'Machine', 'Amount', 'Status', 'Created'],
  },
  payments: {
    title: 'Payments',
    description: 'Review payment transactions and their status.',
    columns: ['Payment ID', 'Order', 'Provider', 'Amount', 'Status'],
  },
}

function formatDate(value) {
  if (!value) return 'Not reported'
  return new Date(value).toLocaleString()
}

function StatusBadge({ value }) {
  const status = String(value || 'unknown').toLowerCase()

  return (
    <span className={`badge badge-${status.replace(/\s+/g, '-')}`}>
      <span className="status-dot" />
      {value || 'Unknown'}
    </span>
  )
}

function App() {
  const [activePage, setActivePage] = useState('overview')
  const [machines, setMachines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [lastUpdated, setLastUpdated] = useState(null)

  async function loadMachines() {
    try {
      setError('')
      const response = await fetch(API_URL)

      if (!response.ok) {
        throw new Error('Unable to load machines')
      }

      const data = await response.json()
      setMachines(Array.isArray(data) ? data : data.results ?? [])
      setLastUpdated(new Date())
    } catch {
      setError('Could not connect to Django. Check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMachines()
  }, [])

  const onlineCount = machines.filter(
    item => item.status?.toLowerCase() === 'online'
  ).length

  const offlineCount = machines.filter(
    item => item.status?.toLowerCase() === 'offline'
  ).length

  const attentionCount = machines.filter(item =>
    ['warning', 'fault'].includes(item.machine_condition?.toLowerCase())
  ).length

  const filteredMachines = useMemo(() => {
    return machines.filter(machine => {
      const matchesSearch = [
        machine.machine_code,
        machine.location,
        machine.status,
      ].some(value => String(value || '').toLowerCase().includes(search.toLowerCase()))

      const matchesStatus =
        statusFilter === 'all' ||
        machine.status?.toLowerCase() === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [machines, search, statusFilter])

  const currentLabel = navigation
    .flatMap(group => group.items)
    .find(item => item.id === activePage)?.label || 'Overview'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">W</div>
          <div>
            <h2>WaterFlow</h2>
            <span>MANAGEMENT</span>
          </div>
        </div>

        <div className="company-label">WORKSPACE</div>

        <div className="workspace">
          <div className="workspace-icon">WF</div>
          <div className="workspace-info">
            <strong>Water Company</strong>
            <span>Owner dashboard</span>
          </div>
          <span className="workspace-arrow">⌄</span>
        </div>

        <nav className="navigation">
          {navigation.map(group => (
            <div className="nav-group" key={group.group}>
              <p className="nav-heading">{group.group}</p>

              {group.items.map(item => (
                <button
                  key={item.id}
                  className={`nav-item ${activePage === item.id ? 'selected' : ''}`}
                  onClick={() => setActivePage(item.id)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>
                  {item.id === 'machines' && (
                    <span className="nav-count">{machines.length}</span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-indicator">
            <span className={`connection-dot ${error ? 'disconnected' : ''}`} />
            <div>
              <strong>{error ? 'Backend disconnected' : 'Dashboard service'}</strong>
              <span>{error ? 'Check connection' : 'Connection status'}</span>
            </div>
          </div>
          <div className="profile">
            <div className="avatar">OW</div>
            <div className="profile-info">
              <strong>Company Owner</strong>
              <span>Administrator</span>
            </div>
            <span className="profile-menu">•••</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{currentLabel}</strong>
          </div>

          <div className="topbar-actions">
            <span className="live-label">
              <span className="live-dot" />
              Live data
            </span>
            <button className="icon-button" title="Refresh data" onClick={loadMachines}>
              ↻
            </button>
            <div className="top-avatar">OW</div>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="error-banner">
              <span>{error}</span>
              <button onClick={loadMachines}>Retry</button>
            </div>
          )}

          {activePage === 'overview' && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">BUSINESS OVERVIEW</p>
                  <h1>Dashboard</h1>
                  <p className="page-description">
                    Monitor your water vending operations from one place.
                  </p>
                </div>
                <button className="primary-button" onClick={() => setActivePage('machines')}>
                  View machines <span>→</span>
                </button>
              </div>

              <section className="metric-grid">
                <MetricCard
                  title="Total machines"
                  value={loading ? '—' : machines.length}
                  icon="▤"
                  tone="blue"
                  note="Registered in the system"
                />
                <MetricCard
                  title="Online machines"
                  value={loading ? '—' : onlineCount}
                  icon="◉"
                  tone="green"
                  note="Currently marked online"
                />
                <MetricCard
                  title="Offline machines"
                  value={loading ? '—' : offlineCount}
                  icon="⊘"
                  tone="orange"
                  note="Currently marked offline"
                />
                <MetricCard
                  title="Needs attention"
                  value={loading ? '—' : attentionCount}
                  icon="!"
                  tone="red"
                  note="Warning or fault reported"
                />
              </section>

              <section className="content-grid">
                <div className="panel machine-panel">
                  <div className="panel-header">
                    <div>
                      <h2>Machine status</h2>
                      <p>Current status from your backend</p>
                    </div>
                    <button className="text-button" onClick={() => setActivePage('machines')}>
                      View all <span>→</span>
                    </button>
                  </div>

                  {loading ? (
                    <EmptyState title="Loading machines..." />
                  ) : machines.length === 0 && !error ? (
                    <EmptyState title="No machines registered" />
                  ) : (
                    <div className="machine-list">
                      {machines.slice(0, 5).map(machine => (
                        <div className="machine-row" key={machine.id}>
                          <div className="machine-symbol">▤</div>
                          <div className="machine-details">
                            <strong>{machine.machine_code}</strong>
                            <span>{machine.location || 'Location not set'}</span>
                          </div>
                          <StatusBadge value={machine.status} />
                          <button
                            className="row-arrow"
                            onClick={() => setActivePage('machines')}
                            aria-label="View machines"
                          >
                            →
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="panel-footer">
                    <span>
                      {lastUpdated
                        ? `Last refreshed ${lastUpdated.toLocaleTimeString()}`
                        : 'Waiting for data'}
                    </span>
                    <button className="text-button" onClick={loadMachines}>Refresh ↻</button>
                  </div>
                </div>

                <div className="panel health-panel">
                  <div className="panel-header">
                    <div>
                      <h2>Machine health</h2>
                      <p>Reported condition</p>
                    </div>
                    <span className="small-icon">⌁</span>
                  </div>

                  <div className="health-summary">
                    <div className="health-number">{loading ? '—' : machines.length}</div>
                    <div className="health-caption">Registered machines</div>
                  </div>

                  <div className="health-line">
                    <span className="health-key"><i className="key-green" /> Normal</span>
                    <strong>{loading ? '—' : machines.filter(m => m.machine_condition === 'normal').length}</strong>
                  </div>
                  <div className="health-line">
                    <span className="health-key"><i className="key-orange" /> Warning</span>
                    <strong>{loading ? '—' : machines.filter(m => m.machine_condition === 'warning').length}</strong>
                  </div>
                  <div className="health-line">
                    <span className="health-key"><i className="key-red" /> Fault</span>
                    <strong>{loading ? '—' : machines.filter(m => m.machine_condition === 'fault').length}</strong>
                  </div>
                  <div className="health-line">
                    <span className="health-key"><i className="key-gray" /> Unknown</span>
                    <strong>{loading ? '—' : machines.filter(m => !m.machine_condition || m.machine_condition === 'unknown').length}</strong>
                  </div>
                </div>
              </section>

              <section className="panel telemetry-panel">
                <div className="panel-header">
                  <div>
                    <h2>Water levels & stock</h2>
                    <p>Available readings reported by each machine</p>
                  </div>
                  <button className="text-button" onClick={() => setActivePage('inventory')}>
                    Inventory <span>→</span>
                  </button>
                </div>

                {loading ? (
                  <EmptyState title="Loading readings..." />
                ) : machines.length === 0 ? (
                  <EmptyState title="No machine data available" />
                ) : (
                  <div className="telemetry-grid">
                    {machines.slice(0, 4).map(machine => (
                      <div className="telemetry-card" key={machine.id}>
                        <div className="telemetry-top">
                          <strong>{machine.machine_code}</strong>
                          <StatusBadge value={machine.machine_condition || 'unknown'} />
                        </div>
                        <div className="telemetry-value">
                          {machine.water_level_percent == null
                            ? '—'
                            : `${machine.water_level_percent}%`}
                        </div>
                        <div className="telemetry-label">Water level</div>
                        <div className="progress-track">
                          <div
                            className="progress-fill"
                            style={{
                              width: `${Math.max(0, Math.min(100, Number(machine.water_level_percent) || 0))}%`,
                            }}
                          />
                        </div>
                        <div className="telemetry-bottom">
                          <span>Cups in stock</span>
                          <strong>{machine.cups_quantity ?? '—'}</strong>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}

          {activePage === 'machines' && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">OPERATIONS</p>
                  <h1>Machines</h1>
                  <p className="page-description">Manage and monitor registered vending machines.</p>
                </div>
                <button className="primary-button" onClick={loadMachines}>↻ Refresh data</button>
              </div>

              <section className="metric-grid compact-grid">
                <MetricCard title="All machines" value={loading ? '—' : machines.length} icon="▤" tone="blue" />
                <MetricCard title="Online" value={loading ? '—' : onlineCount} icon="◉" tone="green" />
                <MetricCard title="Offline" value={loading ? '—' : offlineCount} icon="⊘" tone="orange" />
              </section>

              <section className="panel table-panel">
                <div className="table-toolbar">
                  <div>
                    <h2>All machines</h2>
                    <p>{machines.length} registered machine(s)</p>
                  </div>
                  <div className="table-controls">
                    <input
                      type="search"
                      placeholder="Search code or location..."
                      value={search}
                      onChange={event => setSearch(event.target.value)}
                    />
                    <select value={statusFilter} onChange={event => setStatusFilter(event.target.value)}>
                      <option value="all">All statuses</option>
                      <option value="online">Online</option>
                      <option value="offline">Offline</option>
                      <option value="maintenance">Maintenance</option>
                    </select>
                  </div>
                </div>

                {loading ? (
                  <EmptyState title="Loading machines..." />
                ) : filteredMachines.length === 0 ? (
                  <EmptyState title={error ? 'Unable to load machines' : 'No matching machines'} />
                ) : (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Machine</th>
                          <th>Location</th>
                          <th>Status</th>
                          <th>Condition</th>
                          <th>Water level</th>
                          <th>Cups</th>
                          <th>Last seen</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredMachines.map(machine => (
                          <tr key={machine.id}>
                            <td>
                              <strong className="table-machine-code">{machine.machine_code}</strong>
                              <span className="table-subtext">ID: {machine.id}</span>
                            </td>
                            <td>{machine.location || 'Not set'}</td>
                            <td><StatusBadge value={machine.status} /></td>
                            <td><StatusBadge value={machine.machine_condition || 'unknown'} /></td>
                            <td>{machine.water_level_percent == null ? '—' : `${machine.water_level_percent}%`}</td>
                            <td>{machine.cups_quantity ?? '—'}</td>
                            <td>{formatDate(machine.last_seen_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}

          {sectionInfo[activePage] && (
            <DataSection
              info={sectionInfo[activePage]}
              onRefresh={loadMachines}
            />
          )}

          {activePage === 'analytics' && (
            <ComingSoon
              title="Analytics"
              description="Sales, machine usage and revenue reports will appear here once the relevant API data is connected."
              icon="▥"
            />
          )}

          {activePage === 'settings' && (
            <section className="panel settings-panel">
              <div className="page-heading settings-heading">
                <div>
                  <p className="eyebrow">SYSTEM</p>
                  <h1>Settings</h1>
                  <p className="page-description">Dashboard and backend connection details.</p>
                </div>
              </div>
              <div className="settings-row">
                <div>
                  <strong>Backend API</strong>
                  <p>Machine data endpoint</p>
                </div>
                <code>{API_URL}</code>
              </div>
              <div className="settings-row">
                <div>
                  <strong>Connection</strong>
                  <p>Current dashboard API request</p>
                </div>
                <StatusBadge value={error ? 'Disconnected' : 'Connected'} />
              </div>
              <div className="settings-row">
                <div>
                  <strong>Last refreshed</strong>
                  <p>Most recent successful machine request</p>
                </div>
                <span>{lastUpdated ? lastUpdated.toLocaleString() : 'Not yet refreshed'}</span>
              </div>
              <button className="primary-button settings-refresh" onClick={loadMachines}>
                Test connection / Refresh
              </button>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}

function MetricCard({ title, value, icon, tone, note }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      {note && <div className="metric-note">{note}</div>}
    </div>
  )
}

function EmptyState({ title }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">▤</div>
      <strong>{title}</strong>
    </div>
  )
}

function DataSection({ info, onRefresh }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">MANAGEMENT</p>
          <h1>{info.title}</h1>
          <p className="page-description">{info.description}</p>
        </div>
        <button className="primary-button" onClick={onRefresh}>↻ Refresh</button>
      </div>

      <section className="panel table-panel">
        <div className="table-toolbar">
          <div>
            <h2>{info.title} list</h2>
            <p>Waiting for the corresponding Django API endpoint.</p>
          </div>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>{info.columns.map(column => <th key={column}>{column}</th>)}</tr>
            </thead>
          </table>
        </div>
        <EmptyState title="No live records connected yet" />
        <div className="section-note">
          This section will show database records after its API endpoint is connected.
        </div>
      </section>
    </>
  )
}

function ComingSoon({ title, description, icon }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">BUSINESS</p>
          <h1>{title}</h1>
          <p className="page-description">{description}</p>
        </div>
      </div>
      <section className="panel coming-panel">
        <div className="coming-icon">{icon}</div>
        <h2>{title} reports</h2>
        <p>Analytics will use actual orders and payment records, not sample numbers.</p>
      </section>
    </>
  )
}

export default App
