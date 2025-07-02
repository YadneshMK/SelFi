import { createContext, useContext, useState, HTMLAttributes } from 'react'

const TabsContext = createContext<{ value: string; onChange: (value: string) => void } | null>(null)

export function Tabs({ defaultValue, children, className = '' }: { defaultValue: string; children: React.ReactNode; className?: string }) {
  const [value, setValue] = useState(defaultValue)
  
  return (
    <TabsContext.Provider value={{ value, onChange: setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground ${className}`}>
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children, className = '' }: { value: string; children: React.ReactNode; className?: string }) {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabsTrigger must be used within Tabs')
  
  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        context.value === value ? 'bg-background text-foreground shadow-sm' : ''
      } ${className}`}
      onClick={() => context.onChange(value)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children, className = '' }: { value: string; children: React.ReactNode; className?: string }) {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabsContent must be used within Tabs')
  
  if (context.value !== value) return null
  
  return <div className={`mt-2 ${className}`}>{children}</div>
}