import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './Auth.css'

const Login: React.FC = () => {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('登录失败')
      }

      const data = await response.json()
      
      // 获取用户信息
      const userResponse = await fetch(`${API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      })
      
      if (!userResponse.ok) {
        throw new Error('获取用户信息失败')
      }
      
      const user = await userResponse.json()
      setAuth(user, data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError('邮箱或密码错误')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>登录</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">邮箱</label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        
        <p className="auth-footer">
          还没有账号？<Link to="/register">立即注册</Link>
        </p>
      </div>
    </div>
  )
}

export default Login
