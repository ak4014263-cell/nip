import base64
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger('wttj_microservice')

LIVE_AUTOMATION_STATE: Dict[str, Any] = {
    'is_running': False,
    'step_name': 'Idle',
    'step_index': 0,
    'total_steps': 6,
    'progress': 0,
    'current_url': 'https://www.welcometothejungle.com',
    'logs': [
        {'time': datetime.utcnow().strftime('%H:%M:%S'), 'msg': 'WTTJ Automation Service ready.'}
    ],
    'last_screenshot_base64': '',
    'updated_at': datetime.utcnow().isoformat(),
    'result': None
}

async def update_live_state(step_name, step_index, progress, url, log_msg, page=None, is_running=True):
    global LIVE_AUTOMATION_STATE
    now_str = datetime.utcnow().strftime('%H:%M:%S')
    screenshot_b64 = LIVE_AUTOMATION_STATE.get('last_screenshot_base64', '')
    if page:
        try:
            screenshot_bytes = await page.screenshot(type='jpeg', quality=55)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception:
            pass
    logs = LIVE_AUTOMATION_STATE.get('logs', [])
    logs.append({'time': now_str, 'msg': log_msg})
    if len(logs) > 50:
        logs = logs[-50:]
    LIVE_AUTOMATION_STATE.update({
        'is_running': is_running,
        'step_name': step_name,
        'step_index': step_index,
        'progress': progress,
        'current_url': url,
        'logs': logs,
        'last_screenshot_base64': screenshot_b64,
        'updated_at': datetime.utcnow().isoformat()
    })
    logger.info(f'[LivePreview] {step_name} ({progress}%) - {log_msg}')
