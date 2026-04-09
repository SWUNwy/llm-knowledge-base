/**
 * User-friendly error messages mapped from backend ErrorCode values.
 */

export interface ErrorMessage {
  title: string;
  description: string;
  suggestion?: string;
  action?: { label: string; link: string };
}

const ERROR_MESSAGES: Record<string, ErrorMessage> = {
  // LLM errors
  LLM_API_KEY_INVALID: {
    title: 'API Key \u65e0\u6548',
    description: 'LLM \u670d\u52a1\u8ba4\u8bc1\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5 API Key \u914d\u7f6e\u3002',
    suggestion: '\u8bf7\u524d\u5f80\u8bbe\u7f6e\u9875\u9762\u68c0\u67e5\u5e76\u66f4\u65b0 API Key\u3002',
    action: { label: '\u524d\u5f80\u8bbe\u7f6e', link: '/settings' },
  },
  LLM_QUOTA_EXCEEDED: {
    title: 'API \u914d\u989d\u5df2\u7528\u5b8c',
    description: 'LLM API \u8c03\u7528\u6b21\u6570\u5df2\u8fbe\u4e0a\u9650\u3002',
    suggestion: '\u8bf7\u68c0\u67e5\u8d26\u6237\u4f59\u989d\u6216\u5347\u7ea7\u5957\u9910\u3002',
  },
  LLM_RATE_LIMIT: {
    title: '\u8bf7\u6c42\u8fc7\u4e8e\u9891\u7e41',
    description: 'API \u8c03\u7528\u901f\u7387\u8d85\u9650\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002',
  },
  LLM_TIMEOUT: {
    title: '\u54cd\u5e94\u8d85\u65f6',
    description: 'LLM \u670d\u52a1\u54cd\u5e94\u65f6\u95f4\u8fc7\u957f\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5\u3002',
    suggestion: '\u53ef\u4ee5\u5c1d\u8bd5\u7f29\u77ed\u95ee\u9898\u6216\u7a0d\u540e\u91cd\u8bd5\u3002',
  },
  LLM_SERVICE_DOWN: {
    title: '\u670d\u52a1\u6682\u4e0d\u53ef\u7528',
    description: 'LLM \u670d\u52a1\u5f53\u524d\u65e0\u6cd5\u8fde\u63a5\u3002',
    suggestion: '\u8bf7\u7a0d\u540e\u91cd\u8bd5\uff0c\u6216\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5\u3002',
  },
  LLM_MODEL_NOT_FOUND: {
    title: '\u6a21\u578b\u4e0d\u53ef\u7528',
    description: '\u5f53\u524d\u914d\u7f6e\u7684 LLM \u6a21\u578b\u4e0d\u5b58\u5728\u6216\u4e0d\u53ef\u7528\u3002',
    suggestion: '\u8bf7\u5728\u8bbe\u7f6e\u9875\u9762\u66f4\u6362\u6a21\u578b\u3002',
    action: { label: '\u524d\u5f80\u8bbe\u7f6e', link: '/settings' },
  },

  // Import errors
  IMPORT_INVALID_URL: {
    title: '\u65e0\u6cd5\u8bbf\u95ee\u8be5\u7f51\u5740',
    description: '\u8bf7\u786e\u8ba4\u7f51\u5740\u662f\u5426\u6b63\u786e\u4e14\u53ef\u4ee5\u8bbf\u95ee\u3002',
  },
  IMPORT_FILE_NOT_FOUND: {
    title: '\u6587\u4ef6\u4e0d\u5b58\u5728',
    description: '\u627e\u4e0d\u5230\u6307\u5b9a\u7684\u6587\u4ef6\uff0c\u8bf7\u68c0\u67e5\u8def\u5f84\u3002',
  },
  IMPORT_PARSE_FAILED: {
    title: '\u89e3\u6790\u5931\u8d25',
    description: '\u65e0\u6cd5\u89e3\u6790\u5bfc\u5165\u7684\u5185\u5bb9\uff0c\u8bf7\u68c0\u67e5\u683c\u5f0f\u662f\u5426\u652f\u6301\u3002',
  },

  // Auth errors
  AUTH_INVALID_CREDENTIALS: {
    title: '\u767b\u5f55\u5931\u8d25',
    description: '\u7528\u6237\u540d\u6216\u5bc6\u7801\u4e0d\u6b63\u786e\u3002',
  },
  AUTH_TOKEN_EXPIRED: {
    title: '\u767b\u5f55\u5df2\u8fc7\u671f',
    description: '\u4f1a\u8bdd\u5df2\u8fc7\u671f\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55\u3002',
  },
  AUTH_SETUP_REQUIRED: {
    title: '\u9700\u8981\u521d\u59cb\u5316',
    description: '\u8bf7\u5148\u521b\u5efa\u7ba1\u7406\u5458\u8d26\u6237\u3002',
  },

  // General errors
  NOT_FOUND: {
    title: '\u672a\u627e\u5230',
    description: '\u8bf7\u6c42\u7684\u8d44\u6e90\u4e0d\u5b58\u5728\u3002',
  },
  VALIDATION_ERROR: {
    title: '\u53c2\u6570\u9519\u8bef',
    description: '\u8bf7\u6c42\u53c2\u6570\u6821\u9a8c\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u8f93\u5165\u3002',
  },
  INTERNAL_ERROR: {
    title: '\u51fa\u9519\u4e86',
    description: '\u670d\u52a1\u5668\u9047\u5230\u4e86\u610f\u5916\u9519\u8bef\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002',
  },
};

const FALLBACK: ErrorMessage = {
  title: '\u51fa\u9519\u4e86',
  description: '\u53d1\u751f\u4e86\u672a\u77e5\u9519\u8bef\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002',
};

export function getErrorMessage(code: string | null | undefined): ErrorMessage {
  if (!code) return FALLBACK;
  return ERROR_MESSAGES[code] ?? FALLBACK;
}
