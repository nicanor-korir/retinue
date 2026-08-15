import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combine classNames using clsx and tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a timestamp to a relative time string (e.g., "2 hours ago", "just now")
 */
export function formatRelativeTime(timestamp: string | Date | null | undefined): string {
  // Handle null or undefined timestamps
  if (!timestamp) {
    return 'never';
  }

  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return 'invalid date';
  }

  const now = new Date();
  const secondsAgo = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (secondsAgo < 60) {
    return 'just now';
  }

  const minutesAgo = Math.floor(secondsAgo / 60);
  if (minutesAgo < 60) {
    return `${minutesAgo} minute${minutesAgo > 1 ? 's' : ''} ago`;
  }

  const hoursAgo = Math.floor(minutesAgo / 60);
  if (hoursAgo < 24) {
    return `${hoursAgo} hour${hoursAgo > 1 ? 's' : ''} ago`;
  }

  const daysAgo = Math.floor(hoursAgo / 24);
  if (daysAgo < 7) {
    return `${daysAgo} day${daysAgo > 1 ? 's' : ''} ago`;
  }

  const weeksAgo = Math.floor(daysAgo / 7);
  if (weeksAgo < 4) {
    return `${weeksAgo} week${weeksAgo > 1 ? 's' : ''} ago`;
  }

  const monthsAgo = Math.floor(daysAgo / 30);
  return `${monthsAgo} month${monthsAgo > 1 ? 's' : ''} ago`;
}

/**
 * Format a date to a readable format (e.g., "Jan 15, 2024")
 */
export function formatDate(timestamp: string | Date | null | undefined): string {
  if (!timestamp) {
    return 'N/A';
  }

  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  
  if (isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

/**
 * Format a date and time to a readable format (e.g., "Jan 15, 2024 10:30 AM")
 */
export function formatDateTime(timestamp: string | Date | null | undefined): string {
  if (!timestamp) {
    return 'N/A';
  }

  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  
  if (isNaN(date.getTime())) {
    return 'Invalid Date';
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}
