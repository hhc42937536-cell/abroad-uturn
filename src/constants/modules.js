const e = (...codes) => String.fromCodePoint(...codes);

export const moduleDefinitions = [
  {
    id: 'M1',
    label: '\u8aaa\u8d70\u5c31\u8d70',
    emoji: e(0x1f680),
    description: '2-7\u5929\u5feb\u901f\u884c\u7a0b',
    aliases: ['m1', 'M1', '\u8aaa\u8d70\u5c31\u8d70', '\u81e8\u6642\u51fa\u884c']
  },
  {
    id: 'M2',
    label: '\u5b8c\u6574\u51fa\u570b\u898f\u5283',
    emoji: e(0x2728),
    description: '8\u6b65\u8a73\u7d30\u8a08\u756b\u66f8',
    aliases: ['m2', 'M2', '\u5b8c\u6574\u51fa\u570b\u898f\u5283', '\u5b8c\u6574\u51fa\u570b\u8a08\u756b']
  },
  {
    id: 'M3',
    label: '\u63a2\u7d22\u6700\u4fbf\u5b9c',
    emoji: e(0x2708, 0xfe0f),
    description: '\u6700\u4f4e\u50f9\u76ee\u7684\u5730',
    aliases: ['m3', 'M3', '\u63a2\u7d22\u6700\u4fbf\u5b9c', '\u4fbf\u5b9c\u6a5f\u7968']
  },
  {
    id: 'M4',
    label: '\u7576\u5730\u4ea4\u901a\u653b\u7565',
    emoji: e(0x1f687),
    description: '\u4ea4\u901a\u5361/\u8def\u7dda/App',
    aliases: ['m4', 'M4', '\u7576\u5730\u4ea4\u901a\u653b\u7565', '\u4ea4\u901a']
  },
  {
    id: 'M5',
    label: '\u4f4f\u5bbf\u63a8\u85a6',
    emoji: e(0x1f3e8),
    description: '\u98ef\u5e97/\u5340\u57df\u63a8\u85a6',
    aliases: ['m5', 'M5', '\u4f4f\u5bbf\u63a8\u85a6', '\u4f4f\u5bbf']
  },
  {
    id: 'M6',
    label: '\u884c\u524d\u5fc5\u77e5',
    emoji: e(0x1f6c2),
    description: '\u7c3d\u8b49/\u6d77\u95dc/\u532f\u7387/\u6253\u5305',
    aliases: ['m6', 'M6', '\u884c\u524d\u5fc5\u77e5', '\u884c\u524d\u9808\u77e5']
  },
  {
    id: 'M7',
    label: '\u73fe\u5728\u6700\u592f',
    emoji: e(0x1f525),
    description: '\u71b1\u9580\u73a9\u6cd5/\u5fc5\u8cb7',
    aliases: ['m7', 'M7', '\u73fe\u5728\u6700\u592f', '\u6700\u592f']
  },
  {
    id: 'M8',
    label: '\u8ffd\u661f\u884c\u7a0b\u898f\u5283',
    emoji: e(0x2b50),
    description: '\u6f14\u5531\u6703/\u898b\u9762\u6703',
    aliases: ['m8', 'M8', '\u8ffd\u661f\u884c\u7a0b\u898f\u5283', '\u8ffd\u661f']
  },
  {
    id: 'M9',
    label: '\u8a2d\u5b9a',
    emoji: e(0x2699, 0xfe0f),
    description: '\u51fa\u767c\u5730/\u8aaa\u660e',
    aliases: ['m9', 'M9', '\u8a2d\u5b9a', '\u500b\u4eba\u8a2d\u5b9a']
  }
];

export function findModuleIdByText(text = '') {
  const normalized = text.trim();
  return moduleDefinitions.find((item) =>
    item.id.toLowerCase() === normalized.toLowerCase()
    || item.aliases.some((alias) => alias.toLowerCase() === normalized.toLowerCase())
  )?.id ?? null;
}
