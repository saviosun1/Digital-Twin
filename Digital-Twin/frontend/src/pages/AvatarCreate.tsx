import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './AvatarCreate.css'

const AvatarCreate: React.FC = () => {
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) {
      navigate('/login')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/avatars`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name })
      })

      if (!response.ok) {
        throw new Error('创建失败')
      }

      const avatar = await response.json()
      navigate(`/avatar/${avatar.id}/questionnaire`)
    } catch (error) {
      alert('创建失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="avatar-create">
      <div className="container">
        <div className="create-card">
          <h1>创建数字分身</h1>
          <p className="subtitle">
            给你的分身起个名字，这个名字将被用于与他人交流时的自我介绍
          </p>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">分身名称</label>
              <input
                id="name"
                type="text"
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="例如：小明、爸爸、爷爷"
                required
              />
            </div>

            <div className="tips">
              <h4>💡 提示</h4>
              <ul>
                <li>可以使用真实姓名，也可以使用昵称</li>
                <li>这个名字将出现在与访客的对话中</li>
                <li>后续可以随时修改</li>
              </ul>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading || !name.trim()}
            >
              {loading ? '创建中...' : '下一步：填写问卷'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AvatarCreate
