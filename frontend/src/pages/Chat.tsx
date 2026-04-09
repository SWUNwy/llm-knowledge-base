import { useState, useRef, useEffect, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api, type AskQuestionResponse } from '../services/api';
import { Send, Bot, User, ExternalLink } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  sources?: AskQuestionResponse['sources'];
  error?: unknown;
}

export default function Chat() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const askMutation = useMutation({
    mutationFn: (q: string) => api.askQuestion(q),
    onSuccess: (data: AskQuestionResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
        },
      ]);
    },
    onError: (err) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'error',
          content: '',
          error: err,
        },
      ]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || askMutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: trimmed },
    ]);
    setQuestion('');
    askMutation.mutate(trimmed);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Ask questions about your knowledge base
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <Bot className="w-12 h-12 mx-auto mb-3" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm">Ask a question to get started</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'error' ? (
              <ErrorAlert
                error={msg.error instanceof Error ? msg.error : null}
                variant="card"
                onRetry={() => {
                  const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
                  if (lastUserMsg) {
                    setMessages((prev) => prev.filter((m) => m.id !== msg.id));
                    askMutation.mutate(lastUserMsg.content);
                  }
                }}
              />
            ) : (
              <>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                )}
                <div
                  className={`max-w-[70%] rounded-xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                      <p className="text-xs font-medium text-gray-500">Sources:</p>
                      {msg.sources.map((source) => (
                        <div key={source.id} className="text-xs text-gray-600">
                          <div className="flex items-center gap-1 font-medium">
                            <ExternalLink className="w-3 h-3" />
                            {source.title}
                          </div>
                          <p className="mt-0.5 line-clamp-2">{source.snippet}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </>
            )}
          </div>
        ))}

        {askMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-blue-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="px-8 py-4 border-t border-gray-200 bg-white"
      >
        <div className="flex gap-3 max-w-3xl mx-auto">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            disabled={askMutation.isPending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={askMutation.isPending || !question.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
