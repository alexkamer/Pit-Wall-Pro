'use client';

import { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  title: string;
  icon?: LucideIcon;
  subtitle?: string;
  className?: string;
}

export function SectionHeader({ title, icon: Icon, subtitle, className = '' }: SectionHeaderProps) {
  return (
    <div className={`f1-section-header ${className}`}>
      <div className="flex items-center gap-3">
        {Icon && <Icon className="h-6 w-6" />}
        <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
      </div>
      {subtitle && (
        <p className="text-sm text-white/70 mt-1">{subtitle}</p>
      )}
    </div>
  );
}
