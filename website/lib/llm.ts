// website/lib/llm.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface CompileRequest {
  action: 'compile';
  payload: {
    documents: Array<{ title: string; content: string }>;
    prompt_template: string;
  };
}

export interface QARequest {
  action: 'qa';
  payload: {
    question: string;
    context: Array<{ doc_id: string; snippet: string }>;
  };
}

export async function streamLLM(
  model: string,
  messages: OpenAI.Chat.ChatCompletionMessageParam[]
): Promise<ReadableStream> {
  const stream = await openai.chat.completions.create({
    model,
    messages,
    stream: true,
  });

  // Convert OpenAI stream to Web Stream
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const content = chunk.choices[0]?.delta?.content;
          if (content) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return readable;
}

export function buildCompilePrompt(documents: CompileRequest['payload']['documents']): string {
  const docsText = documents.map(d => `# ${d.title}\n\n${d.content}`).join('\n\n---\n\n');
  return `You are a knowledge base compiler. Convert the following documents into well-structured wiki articles with markdown formatting.

Documents:
${docsText}

Output a compiled wiki article in markdown format. Use proper headings, bullet points, and formatting. Include [[wiki-style links]] for key concepts.`;
}

export function buildQAPrompt(question: string, context: QARequest['payload']['context']): string {
  const contextText = context.map(c => `Document ${c.doc_id}:\n${c.snippet}`).join('\n\n');
  return `Answer the following question based on the provided context from the knowledge base.

Context:
${contextText}

Question: ${question}

Provide a helpful, accurate answer. Cite which documents you used in your answer.`;
}
