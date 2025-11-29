export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const DRIVER_CODES = [
  'VER', 'HAM', 'LEC', 'NOR', 'PER', 'SAI', 'RUS', 'ALO',
  'PIA', 'STR', 'GAS', 'OCO', 'HUL', 'TSU', 'MAG', 'RIC',
  'ALB', 'SAR', 'BOT', 'ZHO'
] as const;

export const SESSION_TYPES = {
  FP1: 'Practice 1',
  FP2: 'Practice 2',
  FP3: 'Practice 3',
  Q: 'Qualifying',
  S: 'Sprint',
  R: 'Race'
} as const;

export const TIRE_COMPOUNDS = {
  SOFT: { name: 'Soft', color: '#FF0000' },
  MEDIUM: { name: 'Medium', color: '#FDB641' },
  HARD: { name: 'Hard', color: '#F0F0F0' },
  INTERMEDIATE: { name: 'Intermediate', color: '#00FF00' },
  WET: { name: 'Wet', color: '#0000FF' }
} as const;
