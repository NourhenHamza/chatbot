"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { ChevronDown, Database } from "lucide-react"
import * as React from "react"

const databases = [
  { value: "PostgreSQL", label: "PostgreSQL", icon: "🐘" },
  { value: "MySQL", label: "MySQL", icon: "🐬" },
  { value: "MongoDB", label: "MongoDB", icon: "🍃" },
]

interface DatabaseSelectorProps {
  variant?: "default" | "blue" | "green" | "gradient"
  defaultValue?: string
  onValueChange?: (value: string) => void
  className?: string
}

export function DatabaseSelector({
  variant = "default",
  defaultValue,
  onValueChange,
  className,
}: DatabaseSelectorProps) {
  const [value, setValue] = React.useState(defaultValue || "")

  const handleValueChange = (newValue: string) => {
    setValue(newValue)
    onValueChange?.(newValue)
  }

  const getVariantStyles = () => {
    switch (variant) {
      case "blue":
        return {
          trigger:
            "bg-slate-600/50 border-slate-500/50 text-white hover:bg-slate-500/60 focus:ring-blue-400/50 backdrop-blur-sm",
          content: "bg-slate-700/95 border-slate-600/50 backdrop-blur-md",
          item: "text-slate-100 hover:bg-slate-600/60 focus:bg-slate-600/60",
        }
      case "green":
        return {
          trigger:
            "bg-emerald-600/50 border-emerald-500/50 text-white hover:bg-emerald-500/60 focus:ring-emerald-400/50 backdrop-blur-sm",
          content: "bg-emerald-700/95 border-emerald-600/50 backdrop-blur-md",
          item: "text-emerald-50 hover:bg-emerald-600/60 focus:bg-emerald-600/60",
        }
      case "gradient":
        return {
          trigger:
            "bg-gradient-to-r from-violet-500/50 to-orange-400/50 border-violet-400/50 text-white hover:from-violet-400/60 hover:to-orange-300/60 focus:ring-violet-400/50 backdrop-blur-sm",
          content: "bg-gradient-to-br from-violet-600/95 to-orange-500/95 border-violet-500/50 backdrop-blur-md",
          item: "text-white hover:bg-white/20 focus:bg-white/20",
        }
      default:
        return {
          trigger:
            "bg-white/80 border-slate-300 text-slate-900 hover:bg-white focus:ring-slate-400/50 dark:bg-slate-800/80 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800 backdrop-blur-sm",
          content: "bg-white/95 border-slate-200 dark:bg-slate-800/95 dark:border-slate-700 backdrop-blur-md",
          item: "text-slate-900 hover:bg-slate-100 focus:bg-slate-100 dark:text-slate-100 dark:hover:bg-slate-700 dark:focus:bg-slate-700",
        }
    }
  }

  const styles = getVariantStyles()

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center gap-3 mb-3">
        <Database className="h-5 w-5 text-current opacity-80" />
        <span className="font-medium text-current">:</span>
      </div>

      <Select value={value} onValueChange={handleValueChange}>
        <SelectTrigger
          className={cn(
            "w-full h-14 px-4 rounded-2xl border-2 transition-all duration-300 ease-out",
            "shadow-lg hover:shadow-xl focus:shadow-xl",
            "text-left font-medium text-lg",
            "focus:ring-4 focus:ring-offset-0",
            styles.trigger,
          )}
        >
          <div className="flex items-center gap-3 flex-1">
            {value && <span className="text-2xl opacity-100">{databases.find((db) => db.value === value)?.icon}</span>}
            <SelectValue placeholder="Choisir une base de données..." className="text-lg font-medium opacity-100" />
          </div>
          <ChevronDown className="h-5 w-5 opacity-70 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </SelectTrigger>

        <SelectContent
          className={cn(
            "rounded-2xl border-2 shadow-2xl p-2 min-w-[var(--radix-select-trigger-width)]",
            "animate-in fade-in-0 zoom-in-95 duration-200",
            styles.content,
          )}
          position="popper"
          sideOffset={8}
        >
          {databases.map((database) => (
            <SelectItem
              key={database.value}
              value={database.value}
              className={cn(
                "rounded-xl px-4 py-3 cursor-pointer transition-all duration-200",
                "focus:outline-none data-[highlighted]:outline-none",
                "font-medium text-base",
                styles.item,
              )}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl opacity-100">{database.icon}</span>
                <span className="opacity-100">{database.label}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
