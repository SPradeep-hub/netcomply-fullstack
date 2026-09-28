import { NavLink } from 'react-router-dom'

export default function Nav({ pendingCount }) {
  return (
    <header>
      <div className="hwrap">
        <div className="logo"><span className="dot" />NetComply</div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink>
          <NavLink to="/upload" className={({ isActive }) => (isActive ? 'active' : '')}>Upload &amp; Scan</NavLink>
          <NavLink to="/training" className={({ isActive }) => (isActive ? 'active' : '')}>
            AI Training{pendingCount ? ` (${pendingCount})` : ''}
          </NavLink>
        </nav>
      </div>
    </header>
  )
}
