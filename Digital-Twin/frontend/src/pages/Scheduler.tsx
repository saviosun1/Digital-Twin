import React from 'react'
import { useParams } from 'react-router-dom'
import './Scheduler.css'

const Scheduler: React.FC = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { avatarId: _avatarId } = useParams<{ avatarId: string }>()

  return (
    <div className="scheduler">
      <div className="container">
        <div className="scheduler-header">
          <h1>定时消息</h1>
          <button className="btn btn-primary">+ 新建消息</button>
        </div>

        <div className="scheduler-empty">
          <div className="empty-icon">⏰</div>
          <h3>暂无定时消息</h3>
          <p>设置生日祝福、纪念日提醒或重要信息传递</p>
        </div>
      </div>
    </div>
  )
}

export default Scheduler
