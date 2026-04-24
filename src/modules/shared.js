import { textMessage } from '../services/line.js';

export function ask(text, nextStep, state = {}) {
  return { done: false, nextStep, state, messages: [withControlQuickReply(textMessage(text))] };
}

export function quickAsk(text, options, nextStep, state = {}) {
  return {
    done: false,
    nextStep,
    state,
    messages: [withControlQuickReply({
      type: 'text',
      text,
      quickReply: {
        items: options.map((option) => ({
          type: 'action',
          action: {
            type: 'message',
            label: option,
            text: option
          }
        }))
      }
    })]
  };
}

export function dateAsk(text, nextStep, state = {}) {
  return {
    done: false,
    nextStep,
    state,
    messages: [withControlQuickReply({
      type: 'text',
      text,
      quickReply: {
        items: [{
          type: 'action',
          action: {
            type: 'datetimepicker',
            label: '選擇日期',
            data: 'action=date',
            mode: 'date'
          }
        }]
      }
    })]
  };
}

export function done(messages) {
  return { done: true, messages: Array.isArray(messages) ? messages : [messages] };
}

export function textValue(message) {
  if (message.type === 'postback') return message.value ?? message.params?.date ?? '';
  return message.text ?? '';
}

export function parseCount(value, fallback = 1) {
  const match = String(value).match(/\d+/);
  return match ? Number(match[0]) : fallback;
}

function withControlQuickReply(message) {
  if (message.type !== 'text') return message;
  const existing = message.quickReply?.items ?? [];
  return {
    ...message,
    quickReply: {
      items: [
        ...existing,
        quickReplyMessage('\u9078\u55ae', '\u9078\u55ae'),
        quickReplyMessage('\u53d6\u6d88', '\u53d6\u6d88')
      ].slice(0, 13)
    }
  };
}

function quickReplyMessage(label, text) {
  return {
    type: 'action',
    action: { type: 'message', label, text }
  };
}
