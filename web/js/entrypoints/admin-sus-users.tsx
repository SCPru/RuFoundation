import React, { useEffect, useState } from 'react'
import useConstCallback from '~util/const-callback'
import { AdminSusUser, fetchAdminSusUsers } from '~api/user'


const AdminSusUsers: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined)
  const [users, setUsers] = useState<AdminSusUser[]>([])

  const loadUsers = useConstCallback(async () => {
    setIsLoading(true)
    try {
      const data = await fetchAdminSusUsers()
      setUsers(data)
    } catch (e: any) {
      setError(e.message || e.error || 'Неизвестная ошибка')
    } finally {
      setIsLoading(false)
    }
  })

  useEffect(() => {
    loadUsers()
  }, [])

  if (error) {
    return (
      <>Не удалось загрузить граф: {error}</>
    )
  }

  if (isLoading) {
    return (
      <>Загрузка...</>
    )
  }

  const userToIp: Record<string, Array<string>> = {}
  const ipToUser: Record<string, Array<string>> = {}

  users.forEach(user => {
    const userName = user.user.name
    const userIp = user.ip
    if (!userToIp[userName]) {
      userToIp[userName] = []
    }
    if (!userToIp[userName].includes(userIp)) {
      userToIp[userName].push(userIp)
    }
    if (!ipToUser[userIp]) {
      ipToUser[userIp] = []
    }
    if (!ipToUser[userIp].includes(userName)) {
      ipToUser[userIp].push(userName)
    }
  })

  console.log({ userToIp, ipToUser })

  return <>
    sus users
  </>
}


export default AdminSusUsers