import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './Dashboard.css'

interface Avatar {
  id: string
  name: string
  status: string
  created_at: string
}

const Dashboard: React.FC = () => {
  const { user, token } = useAuthStore()
  const navigate = useNavigate()
  const [avatars, setAvatars] = useState<Avatar[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }
    fetchAvatars()
  }, [token, navigate])

  const fetchAvatars = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setAvatars(data)
      }
    } catch (error) {
      console.error('Failed to fetch avatars:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="dashboard"><div className="container">加载中...</div></div>
  }

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div>
            <h1>欢迎回来，{user?.name}</h1>
            <p className="text-muted">管理你的数字分身</p>
          </div>
          <Link to="/avatar/create" className="btn btn-primary">
            + 创建新分身
          </Link>
        </div>

        {avatars.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👤</div>
            <h3>还没有数字分身</h3>
            <p>创建你的第一个数字分身，开始记录你的故事</p>
            <Link to="/avatar/create" className="btn btn-primary">
              立即创建
            </Link>
          </div>
        ) : (
          <div className="avatars-grid">
            {avatars.map(avatar => (
              <div key={avatar.id} className="avatar-card">
                <div className="avatar-card-header">
                  <h3>{avatar.name}</h3>
                  <span className={`status-badge ${avatar.status}`}>
                    {avatar.status === 'draft' ? '草稿' : '就绪'}
                  </span>
                </div>
                <p className="avatar-date">
                  创建于 {new Date(avatar.created_at).toLocaleDateString()}
                </p>
                <div className="avatar-actions">
                  <Link 
                    to={`/avatar/${avatar.id}/questionnaire`} 
                    className="btn btn-secondary btn-sm"
                  >
                    编辑问卷
                  </Link>
                  <Link 
                    to={`/chat/${avatar.id}`} 
                    className="btn btn-primary btn-sm"
                  >
                    测试对话
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
