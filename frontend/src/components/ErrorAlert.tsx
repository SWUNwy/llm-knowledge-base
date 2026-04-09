import { AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

import { getErrorMessage } from '../lib/errorMessages';

interface ApiErrorLike {
  code?: string | null;
  message?: string;
}

interface ErrorAlertProps {
  error: ApiErrorLike | Error | null;
  variant?: 'inline' | 'card';
  onRetry?: () => void;
  onDismiss?: () => void;
}

function getErrorCode(error: unknown): string | null {
  if (error && typeof error === 'object' && 'code' in error) {
    return (error as ApiErrorLike).code ?? null;
  }
  return null;
}

function getErrorDescription(error: unknown): string | null {
  if (error && typeof error === 'object' && 'message' in error) {
    return (error as ApiErrorLike).message ?? null;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return null;
}

export default function ErrorAlert({
  error,
  variant = 'inline',
  onRetry,
  onDismiss,
}: ErrorAlertProps) {
  if (!error) return null;

  const code = getErrorCode(error);
  const fallbackDescription = getErrorDescription(error);
  const mapped = getErrorMessage(code);

  const title = mapped.title;
  const description = code ? mapped.description : (fallbackDescription ?? mapped.description);
  const suggestion = mapped.suggestion;
  const action = mapped.action;

  if (variant === 'card') {
    return (
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center shrink-0">
          <AlertCircle className="w-4 h-4 text-red-600" />
        </div>
        <div className="bg-white border border-red-200 rounded-xl px-4 py-3 max-w-[70%]">
          <p className="text-sm font-medium text-red-800">{title}</p>
          <p className="text-sm text-red-600 mt-0.5">{description}</p>
          {suggestion && (
            <p className="text-xs text-gray-500 mt-1.5">{suggestion}</p>
          )}
          <div className="flex items-center gap-3 mt-2">
            {action && (
              <Link
                to={action.link}
                className="text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                {action.label}
              </Link>
            )}
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                重试
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // inline variant
  return (
    <div className="p-3 text-sm bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start gap-2">
        <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-medium text-red-800">{title}</p>
          <p className="text-red-600 mt-0.5">{description}</p>
          {suggestion && (
            <p className="text-xs text-gray-500 mt-1">{suggestion}</p>
          )}
          <div className="flex items-center gap-3 mt-1.5">
            {action && (
              <Link
                to={action.link}
                className="text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                {action.label}
              </Link>
            )}
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                重试
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                关闭
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
