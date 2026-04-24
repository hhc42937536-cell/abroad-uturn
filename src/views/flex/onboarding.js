const airports = [
  ['TPE', '\u6843\u5712'],
  ['TSA', '\u677e\u5c71'],
  ['KHH', '\u9ad8\u96c4'],
  ['RMQ', '\u53f0\u4e2d'],
  ['TNN', '\u53f0\u5357']
];

export function onboardingFlex() {
  return {
    type: 'flex',
    altText: '\u8acb\u9078\u64c7\u9810\u8a2d\u51fa\u767c\u6a5f\u5834',
    contents: {
      type: 'bubble',
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        contents: [
          { type: 'text', text: '\u8a2d\u5b9a\u51fa\u767c\u6a5f\u5834', weight: 'bold', size: 'xl' },
          { type: 'text', text: '\u5148\u9078\u64c7\u5e38\u7528\u51fa\u767c\u5730\uff0c\u4e4b\u5f8c\u67e5\u6a5f\u7968\u6703\u66f4\u5feb\u3002', wrap: true, size: 'sm', color: '#6b7280' },
          {
            type: 'box',
            layout: 'vertical',
            spacing: 'sm',
            contents: airports.map(([code, name]) => ({
              type: 'button',
              style: 'secondary',
              height: 'sm',
              action: {
                type: 'postback',
                label: `${name} ${code}`,
                data: `action=set_departure_airport&value=${code}`,
                displayText: `${name} ${code}`
              }
            }))
          }
        ]
      }
    }
  };
}
