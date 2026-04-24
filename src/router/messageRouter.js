import { findModuleIdByText } from '../constants/modules.js';
import { modules } from '../modules/index.js';
import { ensureUser } from '../repositories/userRepository.js';
import {
  clearSession,
  getSession,
  startSession,
  updateSession
} from '../repositories/sessionRepository.js';
import { getLineProfile, replyFlex, replyMessages, replyText } from '../services/line.js';
import { mainMenuFlex } from '../views/flex/mainMenu.js';
import { onboardingFlex } from '../views/flex/onboarding.js';
import { zh } from '../constants/text.js';
import { updateUserSettings } from '../repositories/userRepository.js';
import { createPriceTrack } from '../repositories/priceTrackingRepository.js';

export async function routeEvent(event) {
  try {
    return await routeEventInternal(event);
  } catch (error) {
    console.error('Failed to route LINE event', error);
    if (event.replyToken && event.replyToken !== '00000000000000000000000000000000') {
      return replyMessages(event.replyToken, [
        { type: 'text', text: '\u7cfb\u7d71\u525b\u525b\u9047\u5230\u554f\u984c\uff0c\u8acb\u91cd\u65b0\u9078\u64c7\u529f\u80fd\u3002' },
        mainMenuFlex()
      ]);
    }
  }
}

async function routeEventInternal(event) {
  if (!event.source?.userId || !event.replyToken) return;

  const lineUserId = event.source.userId;
  const profile = event.type === 'follow' ? await getLineProfile(lineUserId) : null;
  await ensureUser(lineUserId, profile ?? {});

  if (event.type === 'follow') {
    return replyMessages(event.replyToken, [
      { type: 'text', text: '\u6b61\u8fce\u4f7f\u7528\u51fa\u570b\u512a\u8f49\uff01\u5148\u9078\u4e00\u500b\u529f\u80fd\u958b\u59cb\u898f\u5283\u65c5\u7a0b\u3002' },
      onboardingFlex(),
      mainMenuFlex()
    ]);
  }

  const message = normalizeEvent(event);
  if (!message) return replyFlex(event.replyToken, mainMenuFlex());

  if (message.type === 'menu') {
    await clearSession(lineUserId);
    return replyFlex(event.replyToken, mainMenuFlex());
  }

  if (message.type === 'cancel') {
    await clearSession(lineUserId);
    return replyMessages(event.replyToken, [
      { type: 'text', text: zh.cancelled },
      mainMenuFlex()
    ]);
  }

  if (message.type === 'setDepartureAirport') {
    await updateUserSettings(lineUserId, {
      departureAirport: message.value,
      departureCity: airportCity(message.value)
    });
    return replyMessages(event.replyToken, [
      { type: 'text', text: `\u5df2\u8a2d\u5b9a\u51fa\u767c\u6a5f\u5834\uff1a${message.value}` },
      mainMenuFlex()
    ]);
  }

  if (message.type === 'trackPrice') {
    await createPriceTrack(lineUserId, {
      originAirport: message.origin,
      destinationAirport: message.destination,
      lastPriceTwd: message.price
    });
    return replyMessages(event.replyToken, [{
      type: 'text',
      text: `\u5df2\u8ffd\u8e64 ${message.origin} -> ${message.destination}\u3002\u82e5\u4e4b\u5f8c\u6bd4\u76ee\u524d\u50f9\u4f4e\u8d85\u904e 5%\uff0c\u6703\u767c\u9001\u4e00\u5c0d\u4e00\u964d\u50f9\u901a\u77e5\u3002`
    }]);
  }

  if (message.type === 'module') {
    return startModule(event.replyToken, lineUserId, message.value);
  }

  const session = await getSession(lineUserId);
  if (!session) {
    const moduleId = message.type === 'text' ? findModuleIdByText(message.text) : null;
    if (moduleId) return startModule(event.replyToken, lineUserId, moduleId);
    return replyFlex(event.replyToken, mainMenuFlex());
  }

  const module = modules[session.module];
  if (!module) {
    await clearSession(lineUserId);
    return replyFlex(event.replyToken, mainMenuFlex());
  }

  const response = await module.handleStep({
    lineUserId,
    step: session.step,
    state: session.state ?? {},
    message
  });

  if (response.done) {
    await clearSession(lineUserId);
    return replyMessages(event.replyToken, response.messages);
  }

  await updateSession(lineUserId, response.nextStep, response.state);
  return replyMessages(event.replyToken, response.messages);
}

async function startModule(replyToken, lineUserId, moduleId) {
  const module = modules[moduleId];
  if (!module) return replyText(replyToken, zh.unknownModule);

  const first = await module.start({ lineUserId });
  await startSession(lineUserId, moduleId, first.nextStep ?? 1, first.state ?? {});
  return replyMessages(replyToken, first.messages);
}

function normalizeEvent(event) {
  if (event.type === 'postback') {
    const params = new URLSearchParams(event.postback.data);
    const action = params.get('action');
    if (action === 'module') return { type: 'module', value: params.get('id') };
    if (action === 'set_departure_airport') return { type: 'setDepartureAirport', value: params.get('value') };
    if (action === 'track_price') {
      return {
        type: 'trackPrice',
        origin: params.get('origin') ?? 'TPE',
        destination: params.get('destination'),
        price: Number(params.get('price')) || null
      };
    }
    return {
      type: 'postback',
      action,
      value: params.get('value'),
      params: event.postback.params ?? {}
    };
  }

  if (event.type !== 'message') return null;
  if (event.message.type === 'text') {
    const text = event.message.text.trim();
    if (['menu', 'start', '\u9078\u55ae', '\u958b\u59cb', '\u4e3b\u9078\u55ae'].includes(text.toLowerCase())) {
      return { type: 'menu' };
    }
    if (['cancel', 'stop', '\u53d6\u6d88', '\u91cd\u4f86', '\u91cd\u65b0\u958b\u59cb'].includes(text.toLowerCase())) {
      return { type: 'cancel' };
    }
    return { type: 'text', text };
  }
  return null;
}

function airportCity(code) {
  return {
    TPE: '\u53f0\u5317',
    TSA: '\u53f0\u5317',
    KHH: '\u9ad8\u96c4',
    RMQ: '\u53f0\u4e2d',
    TNN: '\u53f0\u5357'
  }[code] ?? '\u53f0\u5317';
}
