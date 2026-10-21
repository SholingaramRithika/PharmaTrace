import { Link } from 'react-router-dom'
export function Stub({ title }: { title: string }) {
  return <div className="max-w-3xl mx-auto px-4 py-16"><h1 className="font-head text-3xl">{title}</h1>
    <p className="text-mute mt-4">That page does not exist.</p><Link to="/" className="btn-ghost inline-block mt-6">GO HOME</Link></div>
}
