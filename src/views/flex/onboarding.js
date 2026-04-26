const airports = [
  ['TPE', '桃園', '國際線最多，大多數出國首選'],
  ['TSA', '松山', '市區直達，東京首爾上海最適'],
  ['KHH', '高雄', '南部出發首選，日韓東南亞都方便'],
  ['RMQ', '台中', '中部旅客省去北上時間'],
  ['TNN', '台南', '台南旅客專屬，進出最省時']
];

const palette = [
  { soft: '#EEF2FF', shadow: '#C7D2FE', text: '#283593', main: '#1A1F3A' },
  { soft: '#FFF3EE', shadow: '#FED7AA', text: '#BF360C', main: '#FF8C42' },
  { soft: '#E8F5E9', shadow: '#BBF7D0', text: '#166534', main: '#2E7D32' },
  { soft: '#E1F5FE', shadow: '#BAE6FD', text: '#075985', main: '#0277BD' },
  { soft: '#F3E5F5', shadow: '#E9D5FF', text: '#6B21A8', main: '#8E24AA' }
];

export function onboardingFlex() {
  const rows = [];
  for (let i = 0; i < airports.length; i += 2) {
    const pair = airports.slice(i, i + 2);
    rows.push({
      type: 'box',
      layout: 'horizontal',
      spacing: 'sm',
      contents: [
        ...pair.map(([code, name, note], j) => airportTile(code, name, note, i + j)),
        ...(pair.length === 1 ? [{ type: 'filler' }] : [])
      ]
    });
  }

  return {
    type: 'flex',
    altText: '請選擇預設出發機場',
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '20px',
        contents: [
          { type: 'text', text: '✈️ 設定出發機場', weight: 'bold', size: 'xl', color: '#FFFFFF' },
          {
            type: 'text',
            text: '先選常用出發地，之後查機票會更快。',
            size: 'xs',
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

function airportTile(code, name, note, index) {
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
      label: `${name} ${code}`,
      data: `action=set_departure_airport&value=${code}`,
      displayText: `${name} ${code}`
    },
    contents: [{
      type: 'box',
      layout: 'vertical',
      backgroundColor: color.soft,
      cornerRadius: '12px',
      paddingAll: '12px',
      spacing: 'xs',
      contents: [
        { type: 'text', text: '🛫', size: 'xl', flex: 0 },
        {
          type: 'text',
          text: `${name}（${code}）`,
          size: 'sm',
          weight: 'bold',
          color: color.text,
          wrap: true
        },
        { type: 'text', text: note, size: 'xxs', color: '#64748B', wrap: true },
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
