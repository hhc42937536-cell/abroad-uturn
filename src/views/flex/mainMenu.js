import { moduleDefinitions } from '../../constants/modules.js';
import { zh } from '../../constants/text.js';

export function mainMenuFlex() {
  return {
    type: 'flex',
    altText: `${zh.appName}\u4e3b\u9078\u55ae`,
    contents: {
      type: 'bubble',
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        contents: [
          { type: 'text', text: zh.appName, weight: 'bold', size: 'xl' },
          { type: 'text', text: zh.chooseModule, size: 'sm', color: '#6b7280' },
          {
            type: 'box',
            layout: 'vertical',
            spacing: 'sm',
            contents: moduleDefinitions.map((item) => ({
              type: 'button',
              style: 'secondary',
              height: 'sm',
              action: {
                type: 'postback',
                label: `${item.emoji} ${item.label}`,
                data: `action=module&id=${item.id}`,
                displayText: `${item.emoji} ${item.label}`
              }
            }))
          }
        ]
      }
    }
  };
}
