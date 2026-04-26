import { textMessage } from '../services/line.js';

const accentPalette = [
  { main: '#1A1F3A', soft: '#EEF2FF', shadow: '#C7D2FE', text: '#283593', icon: '✈️' },
  { main: '#FF8C42', soft: '#FFF3EE', shadow: '#FED7AA', text: '#BF360C', icon: '🔥' },
  { main: '#2E7D32', soft: '#E8F5E9', shadow: '#BBF7D0', text: '#166534', icon: '🌿' },
  { main: '#0277BD', soft: '#E1F5FE', shadow: '#BAE6FD', text: '#075985', icon: '💧' },
  { main: '#8E24AA', soft: '#F3E5F5', shadow: '#E9D5FF', text: '#6B21A8', icon: '⭐' },
  { main: '#C62828', soft: '#FFEBEE', shadow: '#FECACA', text: '#991B1B', icon: '📍' },
  { main: '#00695C', soft: '#E0F2F1', shadow: '#99F6E4', text: '#115E59', icon: '🧭' },
  { main: '#F57F17', soft: '#FFFBEA', shadow: '#FEF08A', text: '#854D0E', icon: '💰' }
];

export function ask(text, nextStep, state = {}) {
  return { done: false, nextStep, state, messages: [withControlQuickReply(textMessage(text))] };
}

export function askWithQuickReplies(text, options, nextStep, state = {}) {
  const controls = [quickReplyMessage('選單', '選單'), quickReplyMessage('取消', '取消')];
  return {
    done: false,
    nextStep,
    state,
    messages: [{
      type: 'text',
      text,
      quickReply: {
        items: [
          ...options.slice(0, 13 - controls.length).map((option) => quickReplyMessage(option, option)),
          ...controls
        ]
      }
    }]
  };
}

export function quickAsk(text, options, nextStep, state = {}) {
  return {
    done: false,
    nextStep,
    state,
    messages: [optionCard(text, '選一個最接近的答案繼續。', options)]
  };
}

export function cardAsk(title, subtitle, options, nextStep, state = {}) {
  return {
    done: false,
    nextStep,
    state,
    messages: [optionCard(title, subtitle, options)]
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
            label: '選日期',
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
        quickReplyMessage('選單', '選單'),
        quickReplyMessage('取消', '取消')
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

function optionCard(title, subtitle, options) {
  const normalized = options.map((option) => typeof option === 'string'
    ? { label: option, value: option, displayText: option }
    : { displayText: option.value, ...option });

  return {
    type: 'flex',
    altText: title,
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '16px',
        contents: [
          { type: 'text', text: title, weight: 'bold', size: 'lg', color: '#FFFFFF', wrap: true },
          ...(subtitle ? [{ type: 'text', text: subtitle, size: 'xs', color: '#AAB4D4', wrap: true, margin: 'xs' }] : [])
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        paddingAll: '12px',
        backgroundColor: '#FFFFFF',
        contents: optionRows(normalized.slice(0, 12))
      },
      footer: {
        type: 'box',
        layout: 'horizontal',
        spacing: 'sm',
        backgroundColor: '#FFFFFF',
        contents: [
          controlButton('選單'),
          controlButton('取消')
        ]
      }
    }
  };
}

function optionRows(options) {
  const rows = [];
  for (let index = 0; index < options.length; index += 2) {
    const pair = options.slice(index, index + 2);
    rows.push({
      type: 'box',
      layout: 'horizontal',
      spacing: 'sm',
      contents: pair.map((option, pairIndex) => optionTile(option, index + pairIndex))
    });
    if (pair.length === 1) {
      rows[rows.length - 1].contents.push({ type: 'filler' });
    }
  }
  return rows;
}

function optionTile(option, index) {
  const color = accentPalette[index % accentPalette.length];
  const detail = optionDetail(option);

  return {
    type: 'box',
    layout: 'vertical',
    flex: 1,
    backgroundColor: color.shadow,
    cornerRadius: '12px',
    paddingBottom: '3px',
    action: {
      type: 'postback',
      label: option.label,
      data: `action=choose&value=${encodeURIComponent(option.value)}`,
      displayText: option.displayText ?? option.value
    },
    contents: [{
      type: 'box',
      layout: 'vertical',
      backgroundColor: color.soft,
      cornerRadius: '12px',
      paddingAll: '10px',
      spacing: 'xs',
      contents: [
        {
          type: 'box',
          layout: 'horizontal',
          spacing: 'xs',
          contents: [
            { type: 'text', text: option.icon ?? color.icon, size: 'lg', flex: 0 },
            { type: 'text', text: option.label, size: 'sm', weight: 'bold', color: color.text, wrap: true, flex: 1 }
          ]
        },
        ...(detail ? [{ type: 'text', text: detail, size: 'xxs', color: '#64748B', wrap: true }] : []),
        {
          type: 'box',
          layout: 'horizontal',
          margin: 'xs',
          contents: [
            { type: 'filler' },
            { type: 'text', text: '選擇 ›', size: 'xxs', color: color.main, weight: 'bold', flex: 0 }
          ]
        }
      ]
    }]
  };
}

function optionDetail(option) {
  if (option.note) return option.note;
  if (option.country && option.airport && option.currency) return `${option.country} / ${option.airport} / ${option.currency}`;
  if (option.country && option.currency) return `${option.country} / ${option.currency}`;
  if (option.city && option.value) return `${option.city} / ${option.value}`;
  if (option.airport) return option.airport;
  if (option.currency) return option.currency;
  return '';
}

function controlButton(text) {
  return {
    type: 'button',
    style: 'secondary',
    height: 'sm',
    action: { type: 'message', label: text, text }
  };
}
