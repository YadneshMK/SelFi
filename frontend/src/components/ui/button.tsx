import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

const baseStyles = 'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'

const variants = {
  default: 'bg-indigo-600 text-white hover:bg-indigo-700',
  destructive: 'bg-red-600 text-white hover:bg-red-700',
  outline: 'border border-gray-300 bg-white hover:bg-gray-50',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
  ghost: 'hover:bg-gray-100 hover:text-gray-900',
  link: 'text-indigo-600 underline-offset-4 hover:underline'
}

const sizes = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3',
  lg: 'h-11 rounded-md px-8',
  icon: 'h-10 w-10'
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
}

export function buttonVariants({
  variant = 'default',
  size = 'default',
  className,
}: {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  className?: string
} = {}) {
  return cn(baseStyles, variants[variant], sizes[size], className)
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={buttonVariants({ variant, size, className })}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'