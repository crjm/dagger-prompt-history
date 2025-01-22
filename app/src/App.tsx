import './App.css'
import { useQuery } from '@tanstack/react-query'
import { API_URL, DAGGER_URL } from './consts'
import { Badge } from './components/ui/badge'
import { formatDistanceToNow } from 'date-fns'
import { useState, useEffect } from 'react'

// create a type for this 
// [{"id":1,"session_id":"msg_01EVzGWgG2nc8RZr3s3mum6h","messages":[{"content":"hello, can you help me??","role":"user"}],"response":[{"type":"text","text":"Of course! I'm here to help. What can I assist you with?"}],"model":"claude-3-opus-20240229","stop_reason":"end_turn","content":"","type":"message","role":"assistant","cache_read_input_tokens":0,"input_tokens":14,"output_tokens":19}]

type Event = {
  id: number
  dagger_trace_id: string
  session_id: string
  messages: { content: string; role: string }[]
  response: { type: string; text: string }[]
  model: string
  stop_reason: string
  content: string
  type: string
  role: string
  cache_read_input_tokens: number
  input_tokens: number
  output_tokens: number
  created_at: string
}

function App() {
  const { data, error } = useQuery({
    queryKey: ['events'],
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
    <div className="flex flex-col gap-4 items-center">
      <h1 className="text-2xl font-bold">Chat History</h1>
      <div className="flex flex-col gap-4 text-sm">
        {data?.map((event: Event) => (
          <div key={event.id} className="flex flex-col gap-4 bg-black/30 border border-gray-600 rounded-md shadow-lg p-8">
            <div className="flex justify-between">
            <Badge variant="outline" className="text-orange-400 font-normal border-orange-400 text-sm">{event.model}</Badge>
            <a className="text-blue-300 text-sm" href={`${DAGGER_URL}/wachines/traces/${event.dagger_trace_id}`}>{event.dagger_trace_id}</a>
            </div>
            <When date={event.created_at} />
            <Conversation event={event} />
            <div className="text-gray-200 self-end">Stop Reason: <span className="text-red-400">{event.stop_reason}</span></div>
            <div className="border-t border-gray-600"></div>
            <Metrics event={event} />
          </div>
        ))}
      </div>
    </div>
  )
}

function When({ date }: { date: string }) {
  // make a relative time string with date-fns
  // add an interval to this so the time is updated

  const [relativeTime, setRelativeTime] = useState(formatDistanceToNow(new Date(date)))

  useEffect(() => {
    const interval = setInterval(() => {
      setRelativeTime(formatDistanceToNow(new Date(date)))
    }, 1000)
    return () => clearInterval(interval)
  }, [date])

  return <div title={date} className="flex gap-2 items-center self-end ">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="size-4">
  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
    <div className="text-gray-200">{relativeTime} ago</div>
  </div>
}

function Conversation({ event }: { event: Event }) {
  return (
    <>
    <div>
    {event.messages.map((message, index) => (
      <div key={index + event.dagger_trace_id} className="flex flex-col gap-2">
        {/* <Badge className="text-black w-fit bg-blue-300">{message.role}</Badge> */}
        <div className="text-gray-200">{message.content}</div>
      </div>
    ))}
  </div>
  <div>
    {event.response.map((response, index) => (
      <div key={index + event.dagger_trace_id} className="flex flex-col gap-2">
        {/* <Badge className="text-black w-fit bg-blue-300">{event.role}</Badge> */}
        <div className="text-gray-400">{response.text}</div>
        </div>
      ))}
    </div>
    </>
  )   
}

function Metrics({ event }: { event: Event }) {
  return (
    <div className="flex gap-12 flex-wrap">
      <div>Input Tokens: {event.input_tokens}</div>
      <div>Output Tokens: {event.output_tokens}</div>
      <div>Cache Read Input Tokens: {event.cache_read_input_tokens}</div>
    </div>
  )
}

export default App
