/**
 * MessageInput - Text input for sending messages
 */

import React, { useState, useRef, KeyboardEvent, useEffect } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = "Type your message...",
  autoFocus = false,
}: MessageInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus the input when requested
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      // Small delay to ensure the element is fully rendered
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 300);
    }
  }, [autoFocus]);

  const handleSend = () => {
    if (!content.trim() || disabled) return;

    onSend(content.trim());
    setContent("");

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            "flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600",
            "bg-white dark:bg-gray-800 px-4 py-3",
            "text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "max-h-32 overflow-y-auto transition-[height] duration-100"
          )}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !content.trim()}
          className={cn(
            "flex items-center justify-center w-10 h-10 rounded-lg",
            "bg-blue-600 hover:bg-blue-700 text-white",
            "focus:outline-none focus:ring-2 focus:ring-blue-500",
            "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600",
            "transition-colors"
          )}
          aria-label="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
}
