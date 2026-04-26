import { moduleDefinitions } from '../../constants/modules.js';
import { zh } from '../../constants/text.js';

const palette = [
  { main: '#1A1F3A', soft: '#EEF2FF', shadow: '#C7D2FE', text: '#283593' },
  { main: '#FF8C42', soft: '#FFF3EE', shadow: '#FED7AA', text: '#BF360C' },
  { main: '#2E7D32', soft: '#E8F5E9', shadow: '#BBF7D0', text: '#166534' },
  { main: '#0277BD', soft: '#E1F5FE', shadow: '#BAE6FD', text: '#075985' },
  { main: '#8E24AA', soft: '#F3E5F5', shadow: '#E9D5FF', text: '#6B21A8' },
  { main: '#C62828', soft: '#FFEBEE', shadow: '#FECACA', text: '#991B1B' },
  { main: '#00695C', soft: '#E0F2F1', shadow: '#99F6E4', text: '#115E59' },
  { main: '#F57F17', soft: '#FFFBEA', shadow: '#FEF08A', text: '#854D0E' },
  { main: '#4527A0', soft: '#EDE7F6', shadow: '#DDD6FE', text: '#3730A3' }
];

export function mainMenuFlex() {
  const rows = [];
  for (let i = 0; i < moduleDefinitions.length; i += 2) {
    const pair = moduleDefinitions.slice(i, i + 2);
    rows.push({
      type: 'box',
      layout: 'horizontal',
      spacing: 'sm',
      contents: [
        ...pair.map((m, j) => moduleTile(m, i + j)),
        ...(pair.length === 1 ? [{ type: 'filler' }] : [])
      ]
    });
  }

  return {
    type: 'flex',
    altText: `${zh.appName} 主選單`,
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '20px',
        contents: [
          { type: 'text', text: zh.appName, weight: 'bold', size: 'xxl', color: '#FFFFFF' },
          {
            type: 'text',
            text: zh.chooseModule,
            size: 'sm',
            color: '#AAB4D4',
            margin: 'xs',
            wrap: true
          }
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        paddingAll: '12px',
        backgroundColor: '#F8FAFC',
        contents: rows
      }
    }
  };
}

function moduleTile(m, index) {
  const color = palette[index % palette.length];
  return {
    type: 'box',
    layout: 'vertical',
    flex: 1,
    backgroundColor: color.shadow,
    cornerRadius: '12px',
    paddingBottom: '3px',
    action: {
      type: 'postback',
      label: m.label,
      data: `action=module&id=${m.id}`,
      displayText: `${m.emoji} ${m.label}`
    },
    contents: [{
      type: 'box',
      layout: 'vertical',
      backgroundColor: color.soft,
      cornerRadius: '12px',
      paddingAll: '12px',
      spacing: 'xs',
      contents: [
        { type: 'text', text: m.emoji, size: 'xl', flex: 0 },
        { type: 'text', text: m.label, size: 'sm', weight: 'bold', color: color.text, wrap: true },
        { type: 'text', text: m.description, size: 'xxs', color: '#64748B', wrap: true },
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
