import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './Chat.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

const Chat: React.FC = () => {
  const { avatarId } = useParams<{ avatarId: string }>()
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [avatarName, setAvatarName] = useState('数字分身')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }
    fetchAvatarInfo()
    // 添加欢迎消息
    setMessages([{
      role: 'assistant',
      content: `你好！我是${avatarName}。我已经准备好了，你可以向我提问或聊天。`,
      timestamp: new Date().toISOString()
    }])
  }, [avatarId, token, navigate])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchAvatarInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${avatarId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAvatarName(data.name)
      }
    } catch (error) {
      console.error('Failed to fetch avatar:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // 添加用户消息
    const newMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, newMessage])

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: userMessage,
          avatar_id: avatarId
        })
      })

      if (response.ok) {
        const data = await response.json()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        }])
      } else {
        throw new Error('发送失败')
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，发送消息时出现了错误。请重试。',
        timestamp: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="chat-header">
          <div className="avatar-info">
            <div className="avatar-avatar">👤</div>
            <div>
              <h3>{avatarName}</h3>
              <p className="status">在线</p>
            </div>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div 
              key={index} 
              className={`message ${msg.role}`}
            >
              <div className="message-content">{msg.content}</div>
              <div className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-content typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            className="chat-input"
            placeholder="输入消息..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button 
            className="btn btn-primary" 
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            发送
          </button>
        </div>
      </div>
    </div>
  )
}

export default Chat