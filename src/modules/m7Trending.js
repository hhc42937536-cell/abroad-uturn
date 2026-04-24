import { ask, done, quickAsk, textValue } from './shared.js';

export const m7 = {
  async start() {
    return ask('\u8acb\u8f38\u5165\u76ee\u7684\u5730\uff0c\u6216\u8f38\u5165\u300c\u5168\u7403\u300d\u67e5\u770b\u71b1\u9580\u5167\u5bb9\u3002', 1);
  },

  async handleStep({ step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk('\u985e\u5225\uff1f', ['\u5fc5\u8cb7', '\u71b1\u9580\u73a9\u6cd5', '\u9910\u5ef3', '\u6253\u5361\u666f\u9ede'], 2, { destination: value });

    return done({
      type: 'text',
      text: [
        `${state.destination} \u73fe\u5728\u6700\u592f\uff1a${value}`,
        `\u8cc7\u6599\u65e5\u671f\uff1a${new Date().toISOString().slice(0, 10)}`,
        '1. \u8fd1\u671f\u793e\u7fa4\u71b1\u5ea6\u9ad8\u7684\u5340\u57df\u512a\u5148\u5b89\u6392\u3002',
        '2. \u71b1\u9580\u9910\u5ef3\u5efa\u8b70\u63d0\u524d\u8a02\u4f4d\u3002',
        '3. \u5fc5\u8cb7\u5546\u54c1\u8acb\u6bd4\u50f9\u4e26\u78ba\u8a8d\u9000\u7a05\u9580\u6abb\u3002'
      ].join('\n')
    });
  }
};
