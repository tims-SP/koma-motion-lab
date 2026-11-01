/* Koma Motion Lab · native Cubism HTML controls. Original art is loaded privately. */
(() => {
  'use strict';
  const byId = (id) => document.getElementById(id);
  const state = {lastMotion:null, lastExpression:null, motionClicks:0, expressionClicks:0, screenshots:0};
  const getModel = () => window.__R1999_MODEL;
  const ready = () => !!getModel()?.getModel?.();
  const getState = () => {
    const instance = getModel(), model = instance?.getModel?.();
    return {
      ready: !!model,
      drawableCount: model?.getDrawableCount?.() ?? null,
      parameterCount: model?.getParameterCount?.() ?? null,
      modelCanvasSize: model ? [model.getCanvasWidth(),model.getCanvasHeight()] : null,
      paused: !!window.__R1999_PAUSED,
      ...state
    };
  };
  function setStatus(message) {
    const el = byId('r1999-status');
    if (el) el.textContent = message;
  }
  function playMotion(group) {
    if (!ready()) return false;
    const result = getModel().startMotion(group,0,3);
    state.lastMotion = group;
    state.motionClicks++;
    setStatus('动作: ' + group);
    return result !== undefined && result !== -1;
  }
  function setExpression(id) {
    if (!ready()) return false;
    getModel().setExpression(id);
    state.lastExpression = id;
    state.expressionClicks++;
    setStatus('表情: ' + id);
    return true;
  }
  function pauseToggle() {
    window.__R1999_PAUSED = !window.__R1999_PAUSED;
    const el=byId('r1999-pause');
    if(el) el.textContent = window.__R1999_PAUSED ? '继续' : '暂停';
    return window.__R1999_PAUSED;
  }
  function capturePNG() {
    const canvas=document.querySelector('canvas');
    if(!canvas) return false;
    const uri=canvas.toDataURL('image/png');
    if(!uri.startsWith('data:image/png;base64,')) return false;
    const a=document.createElement('a');
    a.download='r1999-native-'+Date.now()+'.png';
    a.href=uri;
    document.body.appendChild(a);a.click();a.remove();
    state.screenshots++;
    return true;
  }
  document.addEventListener('DOMContentLoaded', () => {
    byId('r1999-motions')?.addEventListener('click', (e) => {
      const target=e.target.closest('[data-motion]');
      if(target) playMotion(target.dataset.motion);
    });
    byId('r1999-expressions')?.addEventListener('change', (e) => {
      setExpression(e.target.value);
    });
    byId('r1999-pause')?.addEventListener('click',pauseToggle);
    byId('r1999-png')?.addEventListener('click',capturePNG);
    const update = () => {
      const data=getState();
      const indicator=byId('r1999-runtime');
      if(indicator) indicator.textContent=data.ready ?
        `已加载 · ArtMesh ${data.drawableCount} · 参数 ${data.parameterCount}` :
        '原生模型正在加载';
      for(const el of document.querySelectorAll('[data-motion]')) el.disabled=!data.ready;
      const expressions=byId('r1999-expressions');
      if(expressions) expressions.disabled=!data.ready;
    };
    update();
    window.__R1999_INTERVAL = setInterval(update,500);
  });
  window.__R1999_REVIEW={getState, playMotion, setExpression, pauseToggle, capturePNG};
})();
