import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore, API_URL } from '../stores/auth'
import './Questionnaire.css'

interface Question {
  id: string
  category: string
  question: string
}

interface Answer {
  question: string
  answer: string
  category: string
}

const Questionnaire: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerText, setAnswerText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }
    fetchQuestions()
    fetchProgress()
  }, [id, token, navigate])

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`${API_URL}/questions`)
      if (response.ok) {
        const data = await response.json()
        setQuestions(data)
      }
    } catch (error) {
      console.error('Failed to fetch questions:', error)
    }
  }

  const fetchProgress = async () => {
    try {
      const response = await fetch(`${API_URL}/avatars/${id}/questionnaire`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAnswers(data.answers || {})
        // 找到第一个未回答的问题
        const answeredIds = Object.keys(data.answers || {})
        const firstUnanswered = questions.findIndex(q => !answeredIds.includes(q.id))
        setCurrentIndex(firstUnanswered >= 0 ? firstUnanswered : 0)
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error)
    } finally {
      setLoading(false)
    }
  }

  const currentQuestion = questions[currentIndex]
  const progress = questions.length > 0 ? (Object.keys(answers).length / questions.length) * 100 : 0

  const handleSave = async () => {
    if (!currentQuestion || !answerText.trim()) return

    setSaving(true)
    try {
      const response = await fetch(`${API_URL}/avatars/${id}/answers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          question: currentQuestion.question,
          answer: answerText,
          category: currentQuestion.category
        })
      })

      if (response.ok) {
        setAnswers({
          ...answers,
          [currentQuestion.id]: {
            question: currentQuestion.question,
            answer: answerText,
            category: currentQuestion.category
          }
        })
        setAnswerText('')
        
        // 下一个问题
        if (currentIndex < questions.length - 1) {
          setCurrentIndex(currentIndex + 1)
        } else {
          navigate('/dashboard')
        }
      }
    } catch (error) {
      console.error('Failed to save answer:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleSkip = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setAnswerText('')
    } else {
      navigate('/dashboard')
    }
  }

  if (loading || !currentQuestion) {
    return <div className="questionnaire"><div className="container">加载中...</div></div>
  }

  return (
    <div className="questionnaire">
      <div className="container">
        <div className="questionnaire-header">
          <h1>填写问卷</h1>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="progress-text">{Object.keys(answers).length} / {questions.length} 已完成</p>
        </div>

        <div className="question-card">
          <div className="question-number">问题 {currentIndex + 1}</div>
          <h3>{currentQuestion.question}</h3>
          <textarea
            className="textarea"
            placeholder="请输入你的回答..."
            rows={4}
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
          />
          <div className="question-actions">
            <button className="btn btn-secondary" onClick={handleSkip}>跳过</button>
            <button 
              className="btn btn-primary" 
              onClick={handleSave}
              disabled={saving || !answerText.trim()}
            >
              {saving ? '保存中...' : '保存并继续'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Questionnaire