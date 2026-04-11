import { useState, useRef, useEffect, useCallback, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type AskQuestionResponse } from '../services/api';
import { Send, Bot, User, ExternalLink, Loader2, History } from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  sources?: AskQuestionResponse['sources'];
  error?: unknown;
}

interface QAHistoryItem {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

export default function Chat() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: historyData } = useQuery({
    queryKey: ['qa-history'],
    queryFn: () => api.getQAHistory(1, 50),
    enabled: showHistory,
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const streamAnswer = useCallback(async (questionText: string, assistantId: string) => {
    setIsStreaming(true);
    const decoder = new TextDecoder();

    try {
      const reader = await api.askQuestionStream(questionText);
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);

              if (data.error) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, role: 'error', error: new Error(data.error.message || 'Stream error') }
                      : m,
                  ),
                );
                return;
              }

              if (data.chunk) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + data.chunk }
                      : m,
                  ),
                );
              }

              if (data.sources) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, sources: data.sources }
                      : m,
                  ),
                );
              }
            } catch {
              // Incomplete JSON, skip
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, role: 'error', error: err instanceof Error ? err : new Error('Stream failed') }
            : m,
        ),
      );
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isStreaming) return;

    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: trimmed },
      { id: assistantMsgId, role: 'assistant', content: '' },
    ]);
    setQuestion('');
    streamAnswer(trimmed, assistantMsgId);
  };

  const handleRetry = (msgId: string) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx < 0) return;
    const lastUserMsg = [...messages.slice(0, idx)].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;

    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== msgId),
      { id: assistantId, role: 'assistant', content: '' },
    ]);
    streamAnswer(lastUserMsg.content, assistantId);
  };

  return (
    <div className="flex h-full">
      {/* History sidebar */}
      {showHistory && (
        <div className="w-72 border-r border-gray-200 bg-white overflow-y-auto shrink-0">
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900">History</h2>
            <button
              onClick={() => setShowHistory(false)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <History className="w-4 h-4" />
            </button>
          </div>
          <div className="divide-y divide-gray-100">
            {historyData?.items.map((item: QAHistoryItem) => (
              <button
                key={item.id}
                onClick={() => setQuestion(item.question)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
              >
                <p className="text-sm text-gray-900 font-medium truncate">
                  {item.question}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(item.created_at).toLocaleDateString()}
                </p>
              </button>
            ))}
            {historyData?.items.length === 0 && (
              <p className="text-sm text-gray-400 px-4 py-6 text-center">
                No history yet
              </p>
            )}
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="px-8 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Ask questions about your knowledge base
            </p>
          </div>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`p-2 rounded-lg transition-colors ${showHistory ? 'bg-blue-50 text-blue-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'}`}
            title="Toggle history"
          >
            <History className="w-5 h-5" />
          </button>
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
                  onRetry={() => handleRetry(msg.id)}
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
                    <p className="text-sm whitespace-pre-wrap">
                      {msg.content}
                      {msg.role === 'assistant' && isStreaming && msg.content === '' && (
                        <Loader2 className="w-4 h-4 inline-block animate-spin text-gray-400" />
                      )}
                      {msg.role === 'assistant' && isStreaming && msg.content !== '' && (
                        <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse align-text-bottom" />
                      )}
                    </p>

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
              disabled={isStreaming}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isStreaming || !question.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
