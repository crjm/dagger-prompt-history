import { useState } from 'react'
import { Button } from '@/components/ui/button'
import './App.css'
import { useQuery } from '@tanstack/react-query'
import { API_URL } from './consts'

function App() {
  const [count, setCount] = useState(0)

  const { data, error } = useQuery({
    queryKey: ['message'],
    // refetchInterval: 1000,
    queryFn: async () => {
      const response = await fetch(API_URL + '/events')
      if (response.status === 200) {
        return response.json()
      }
    },
  })

  // if (isPending) return <LoadingSpinner />
  if (error) return <div>Error: {error.message}</div>

  return (
    <>
      <h1 className="text-2xl font-bold">Dagger AI</h1>
      <div className="card">
        <Button onClick={() => setCount((count) => count + 1)}>count is {count}</Button>
      </div>
      <div className="flex justify-center items-center">
        {data?.message}
      </div>
    </>
  )
}

export default App
