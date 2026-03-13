import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="container header-content">
          <Link to="/" className="logo">
            Digital Twin
          </Link>
          
          <nav className="nav">
            {user ? (
              <>
                <Link to="/dashboard" className="nav-link">控制台</Link>
                <div className="user-menu">
                  <span className="user-name">{user.name}</span>
                  <button onClick={handleLogout} className="btn btn-secondary btn-sm">
                    退出
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="nav-link">登录</Link>
                <Link to="/register" className="btn btn-primary">注册</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      
      <main className="main">
        {children}
      </main>
      
      <footer className="footer">
        <div className="container">
          <p>&copy; 2026 Digital Twin. 让记忆延续。</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout
