import React, { useEffect, useRef, useState } from 'react'
import useConstCallback from '~util/const-callback'
import { AdminSusUser, fetchAdminSusUsers } from '~api/user'
import styled, { createGlobalStyle } from 'styled-components'
import { SigmaContainer, useLoadGraph, useRegisterEvents, useSigma } from '@react-sigma/core'
import Graph from 'graphology'
import forceAtlas2 from 'graphology-layout-forceatlas2';
import random from 'graphology-layout/random'
import seedrandom from 'seedrandom'
import { SigmaNodeEventPayload } from 'sigma/types'

const Wrapper = createGlobalStyle`
  .w-admin-sus-users {
    width: 100%;
    height: 100%; 
  }
  
  .content-wrapper {
    display: flex;
    flex-direction: column;
  }
  
  .content-wrapper .content:nth-child(2) {
    flex-grow: 1;
    position: relative;
  }
  
  .sigma-container {
      width: 100%;
      height: 100%;
  }
`

const MainView = styled.div`
  display: grid;
  grid-template-rows: min-content 1fr;
  grid-template-columns: 1fr 300px 300px;
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  padding: 32px;
  gap: 16px;
`

const ItemsColumn = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 1fr min-content 1fr; 
  gap: 8px;
`

const SettingsRow = styled.div`
  grid-column: span 3;
  display: flex;
  gap: 16px;
  align-items: center;
`

const USER_COLOR = '#cc0000'
const USER_COLOR_STRONG = '#ff0000'
const USER_COLOR_DIM = '#770000'
const IP_COLOR = '#00cc00'
const IP_COLOR_STRONG = '#00ff00'
const IP_COLOR_DIM = '#007700'
const EDGE_COLOR = '#999'

const USER_SIZE = 2
const IP_SIZE = 1

const AdminSusUsersGraph: React.FC<{userToIp: Record<string, string[]>, ipToUser: Record<string, string[]>, ignoredUsers: string[], ignoredIPs: string[], userFilter: string}> = ({ userToIp, ipToUser, ignoredUsers, ignoredIPs, userFilter }) => {
  const loadGraph = useLoadGraph()
  const registerEvents = useRegisterEvents()
  const sigma = useSigma()
  const [lastNodeSizeFactor, setLastNodeSizeFactor] = useState(1)

  const isSelectedUser = useConstCallback((userName: string) => {
    return userFilter && userName.toLowerCase().includes(userFilter.toLowerCase())
  })

  const filterUserName = useConstCallback((userName: string) => {
    return !ignoredUsers.includes(userName) &&
      (!userFilter || isSelectedUser(userName))
  })

  const updateGraph = useConstCallback(() => {
    const graph = new Graph()

    const susIPAddresses = Object.entries(ipToUser).filter(([k, v]) => {
      return !ignoredIPs.includes(k) && (userFilter ? v.filter(filterUserName).length > 0 : v.filter(filterUserName).length > 1)
    }).map(x => x[0])

    const susUsers = Object.entries(userToIp).filter(([k, v]) => {
      return v.some(x => susIPAddresses.includes(x))
    }).map(x => x[0])

    const filteredIpToUser =
      Object.fromEntries(Object.entries(ipToUser).filter(([k, v]) => {
        return !ignoredIPs.includes(k) && (susIPAddresses.includes(k) || v.some(x => susUsers.includes(x)))
      }))

    const filteredUserToIp =
      Object.fromEntries(Object.entries(userToIp).filter(([k, v]) => {
        return !ignoredUsers.includes(k) && v.some(x => Boolean(filteredIpToUser[x]))
      }))

    const nodeSizeFactor = Math.min(16, 100 / Math.sqrt((Object.keys(filteredUserToIp).length + Object.keys(filteredIpToUser).length)))
    setLastNodeSizeFactor(nodeSizeFactor)

    Object.keys(filteredUserToIp).forEach((user) => {
      const isSelected = isSelectedUser(user)
      graph.addNode(`user:${user}`, {
        x: 0,
        y: 0,
        label: user,
        color: isSelected ? USER_COLOR_STRONG : (userFilter ? USER_COLOR_DIM : USER_COLOR),
        size: USER_SIZE * nodeSizeFactor * (isSelected ? 2 : 1)
      })
    })

    Object.keys(filteredIpToUser).forEach((ip) => {
      graph.addNode(`ip:${ip}`, {
        x: 0,
        y: 0,
        label: ip,
        color: userFilter ? IP_COLOR_DIM : IP_COLOR,
        size: IP_SIZE * nodeSizeFactor
      })
    })

    Object.entries(filteredUserToIp).forEach(([user, ips]) => {
      ips.forEach(ip => {
        if (filteredUserToIp[user] && filteredIpToUser[ip]) {
          graph.addEdge(`user:${user}`, `ip:${ip}`, { color: EDGE_COLOR })
        }
      })
    })

    const rng = seedrandom('static')
    random.assign(graph, { rng })

    const settings = forceAtlas2.inferSettings(graph)

    forceAtlas2.assign(graph, {
      iterations: 100,
      settings
    })

    loadGraph(graph)
  })

  useEffect(() => {
    updateGraph()
  }, [loadGraph, userToIp, ipToUser])

  const isNodeUser = useConstCallback((node: string) => {
    return node.startsWith('user:')
  })

  const onClickNode = useConstCallback((event: SigmaNodeEventPayload) => {
    const { node } = event
    const graph = sigma.getGraph()

    graph.forEachNode((n) => {
      graph.setNodeAttribute(n, 'color', '#ccc')
      graph.setNodeAttribute(n, 'size', lastNodeSizeFactor)
    })

    graph.setNodeAttribute(node, 'color', isNodeUser(node) ? USER_COLOR_STRONG : IP_COLOR_STRONG)
    graph.setNodeAttribute(node, 'size', (isNodeUser(node) ? USER_SIZE : IP_SIZE) * lastNodeSizeFactor * 2)
    graph.forEachNeighbor(node, (neighbor) => {
      if (isNodeUser(neighbor) || graph.neighbors(neighbor).length > 1) {
        graph.setNodeAttribute(neighbor, 'color', isNodeUser(neighbor) ? USER_COLOR_STRONG : IP_COLOR_STRONG)
        graph.setNodeAttribute(neighbor, 'size', (isNodeUser(neighbor) ? USER_SIZE : IP_SIZE) * lastNodeSizeFactor * 2)
        graph.forEachNeighbor(neighbor, (secondLevel) => {
          graph.setNodeAttribute(secondLevel, 'color', isNodeUser(secondLevel) ? USER_COLOR_STRONG : IP_COLOR_STRONG)
          graph.setNodeAttribute(secondLevel, 'size', (isNodeUser(secondLevel) ? USER_SIZE : IP_SIZE) * lastNodeSizeFactor * 2)
        })
      }
    })

    graph.forEachEdge((edge) => {
      graph.setEdgeAttribute(edge, 'color', '#ccc')
    })

    graph.forEachEdge(node, (edge) => {
      graph.setEdgeAttribute(edge, 'color', '#FF00FF')
      graph.forEachNeighbor(node, (neighbor) => {
        if (graph.neighbors(neighbor).length > 1) {
          graph.forEachEdge(neighbor, (secondLevel) => {
            graph.setEdgeAttribute(secondLevel, 'color', '#FF00FF')
          })
        }
      })
    })

    sigma.refresh()
  })

  const onClickStage = useConstCallback(() => {
    const graph = sigma.getGraph()

    graph.forEachNode((n) => {
      if (isNodeUser(n)) {
        const isSelected = isSelectedUser(n.substring(5))
        graph.setNodeAttribute(n, 'color', isSelected ? USER_COLOR_STRONG : (userFilter ? USER_COLOR_DIM : USER_COLOR))
        graph.setNodeAttribute(n, 'size', USER_SIZE * lastNodeSizeFactor * (isSelected ? 2 : 1))
      } else {
        graph.setNodeAttribute(n, 'color', userFilter ? IP_COLOR_DIM : IP_COLOR)
        graph.setNodeAttribute(n, 'size', IP_SIZE * lastNodeSizeFactor)
      }
    })

    graph.forEachEdge((edge) => {
      graph.setEdgeAttribute(edge, 'color', EDGE_COLOR)
    })

    sigma.refresh()
  })

  useEffect(() => {
    registerEvents({
      clickNode: onClickNode,
      clickStage: onClickStage
    })
  }, [registerEvents, sigma, onClickNode, onClickStage])

  return null
}


const AdminSusUsers: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined)
  const [users, setUsers] = useState<AdminSusUser[]>([])
  const [ignoredUsers, setIgnoredUsers] = useState<string[]>([])
  const [ignoredIPs, setIgnoredIPs] = useState<string[]>([])
  const [mask, setMask] = useState(32)

  const allUsersRef = useRef<HTMLSelectElement | null>(null)
  const ignoredUsersRef = useRef<HTMLSelectElement | null>(null)
  const allIPsRef = useRef<HTMLSelectElement | null>(null)
  const ignoredIPsRef = useRef<HTMLSelectElement | null>(null)

  const [userFilter, setUserFilter] = useState('')
  const userSearchRef = useRef<HTMLInputElement | null>(null)

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

  const renderSelect = useConstCallback((ref: React.MutableRefObject<HTMLSelectElement>, items: Record<string, Array<string>>, filterFunc: (item: string) => boolean) => {
    const renderedItems =
      Object.entries(items)
        .filter(([k]) => filterFunc(k))
        .sort(([, v1], [, v2]) => v2.length - v1.length)
    return (
      <select ref={ref} multiple>
        {renderedItems.map(([name, value]) => (
          <option key={name} value={name}>{name} ({value.length})</option>
        ))}
      </select>
    )
  })

  const handleIgnoreUsers = useConstCallback(() => {
    if (!ignoredUsersRef.current || !allUsersRef.current) {
      return
    }
    const usersToIgnore = [...allUsersRef.current.selectedOptions].map(x => x.value)
    setIgnoredUsers(prev => (
      [...prev, ...usersToIgnore]
    ))
  })

  const handleUnignoreUsers = useConstCallback(() => {
    if (!ignoredUsersRef.current || !allUsersRef.current) {
      return
    }
    const usersToUnignore = [...ignoredUsersRef.current.selectedOptions].map(x => x.value)
    setIgnoredUsers(prev => prev.filter(x => !usersToUnignore.includes(x)))
  })

  const handleIgnoreIPs = useConstCallback(() => {
    if (!ignoredIPsRef.current || !allIPsRef.current) {
      return
    }
    const ipsToIgnore = [...allIPsRef.current.selectedOptions].map(x => x.value)
    setIgnoredIPs(prev => (
      [...prev, ...ipsToIgnore]
    ))
  })

  const handleUnignoreIPs = useConstCallback(() => {
    if (!ignoredIPsRef.current || !allIPsRef.current) {
      return
    }
    const ipsToUnignore = [...ignoredIPsRef.current.selectedOptions].map(x => x.value)
    setIgnoredIPs(prev => prev.filter(x => !ipsToUnignore.includes(x)))
  })

  const handleChangeMask = useConstCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const option = e.target.selectedOptions[0]
    setMask(Number.parseInt(option?.value ?? '32', 10))
    setIgnoredIPs([])
  })

  const userToIp: Record<string, Array<string>> = {}
  const ipToUser: Record<string, Array<string>> = {}

  users.forEach(user => {
    const userName = user.user.name
    let userIp = user.ip
    if (mask !== 32 && !userIp.includes(':')) {
      const splitIp = userIp.split('.')
      if (mask === 24) {
        userIp = splitIp.slice(0, 3).join('.') + '.0/24'
      } else if (mask === 16) {
        userIp = splitIp.slice(0, 2).join('.') + '.0.0/16'
      } else if (mask === 8) {
        userIp = splitIp.slice(0, 1).join('.') + '.0.0.0/8'
      }
    }
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

  const handleFilterUser = useConstCallback((e: React.FormEvent) => {
    e.preventDefault()
    setUserFilter(userSearchRef.current?.value ?? '')
  })

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

  return (
    <MainView>
      <Wrapper />
      <SettingsRow>
        <label>
          Маска (только IPv4):{' '}
          <select onChange={handleChangeMask}>
            <option value="32">/32</option>
            <option value="24">/24</option>
            <option value="16">/16</option>
            <option value="8">/8</option>
          </select>
        </label>
        <form onSubmit={handleFilterUser}>
          <label>
            Фильтр по имени/IP (Enter, чтобы применить):
            {' '}
            <input type="text" style={{ padding: '8px', height: '32px' }} ref={userSearchRef} />
          </label>
        </form>
      </SettingsRow>
      <SigmaContainer
        style={{ height: '100%', width: '100%' }}
        settings={{
          defaultNodeColor: '#999',
          labelDensity: 0.5,
          allowInvalidContainer: true,
        }}
      >
        <AdminSusUsersGraph userToIp={userToIp} ipToUser={ipToUser} ignoredUsers={ignoredUsers} ignoredIPs={ignoredIPs} userFilter={userFilter} />
      </SigmaContainer>
      <ItemsColumn>
        {renderSelect(ignoredUsersRef, userToIp, (x: string) => ignoredUsers.includes(x))}
        <div>
          <button className="btn btn-info" onClick={handleIgnoreUsers}>
            <span className="fas fa-angle-up" />
            {' '}
            Не считается
          </button>
          {' '}
          <button className="btn btn-info" onClick={handleUnignoreUsers}>
            <span className="fas fa-angle-down" />
            {' '}
            Считается
          </button>
        </div>
        {renderSelect(allUsersRef, userToIp, (x: string) => !ignoredUsers.includes(x))}
      </ItemsColumn>
      <ItemsColumn>
        {renderSelect(ignoredIPsRef, ipToUser, (x: string) => ignoredIPs.includes(x))}
        <div>
          <button className="btn btn-info" onClick={handleIgnoreIPs}>
            <span className="fas fa-angle-up" />
            {' '}
            Не считается
          </button>
          {' '}
          <button className="btn btn-info" onClick={handleUnignoreIPs}>
            <span className="fas fa-angle-down" />
            {' '}
            Считается
          </button>
        </div>
        {renderSelect(allIPsRef, ipToUser, (x: string) => !ignoredIPs.includes(x))}
      </ItemsColumn>
    </MainView>
  )
}


export default AdminSusUsers