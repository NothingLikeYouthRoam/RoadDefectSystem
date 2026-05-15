"""
AI 分析模块 — 调用 OpenAI 兼容 API 对检测记录进行智能分析
"""
import json
import os
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')

DEFAULT_CONFIG = {
    'api_key': '',
    'base_url': 'https://api.siliconflow.cn',
    'model': 'Qwen/Qwen3-8B',
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(api_key: str, base_url: str, model: str):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'api_key': api_key,
            'base_url': base_url.rstrip('/'),
            'model': model,
        }, f, ensure_ascii=False, indent=2)


def _build_url(base_url: str) -> str:
    url = base_url.rstrip('/')
    if not url.endswith('/v1'):
        url += '/v1'
    return url + '/chat/completions'


def _request(cfg, messages, max_tokens=500, timeout=60):
    """底层请求，返回 content 字符串或 {'error': ...}"""
    try:
        url = _build_url(cfg['base_url'])
        resp = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {cfg["api_key"]}',
                'Content-Type': 'application/json',
            },
            json={
                'model': cfg['model'],
                'messages': messages,
                'temperature': 0.3,
                'max_tokens': max_tokens,
            },
            timeout=timeout,
        )
        if resp.status_code != 200:
            try:
                msg = resp.json().get('error', {}).get('message', resp.text[:100])
            except Exception:
                msg = resp.text[:100]
            return {'error': f'API 请求失败 (HTTP {resp.status_code}): {msg}'}
        return resp.json()['choices'][0]['message']['content'].strip()
    except requests.exceptions.Timeout:
        return {'error': '请求超时，请稍后重试'}
    except Exception as e:
        return {'error': f'请求失败: {e}'}


def _record_summary(record) -> str:
    """构建检测记录摘要文本"""
    class_dist = record.get_class_distribution_dict()
    details = record.get_details_list()
    confidences = [d.get('confidence', 0) for d in details] if details else []
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    min_conf = min(confidences) if confidences else 0
    defect_types = list(class_dist.keys()) if class_dist else []
    return f"""检测类型: {record.type}
检测来源: {record.source}
检测目标总数: {record.total_objects}
类别分布: {', '.join(f'{k}({v}个)' for k, v in class_dist.items()) if class_dist else '无'}
平均置信度: {avg_conf:.3f}
最低置信度: {min_conf:.3f}
缺陷类型: {', '.join(defect_types) if defect_types else '无'}
详细列表: {json.dumps(details[:10], ensure_ascii=False) if details else '无'}"""


def test_connection(api_key: str, base_url: str, model: str):
    try:
        url = _build_url(base_url)
        resp = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 5,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True, '连接成功'
        try:
            msg = resp.json().get('error', {}).get('message', resp.text[:100])
        except Exception:
            msg = resp.text[:100]
        return False, f'HTTP {resp.status_code}: {msg}'
    except requests.exceptions.Timeout:
        return False, '连接超时，请检查网络'
    except Exception as e:
        return False, f'连接失败: {e}'


def analyze(record) -> dict:
    """首次分析：返回结构化 JSON"""
    cfg = load_config()
    if not cfg.get('api_key'):
        return {'error': '未配置 API Key，请先在 AI 分析设置中配置'}

    summary = _record_summary(record)
    prompt = f"""你是一位道路工程专家。请根据以下道路缺陷检测数据给出专业分析。

检测数据:
{summary}

请严格按以下 JSON 格式返回（不要 markdown 代码块）:
{{
  "rating": "评级 A/B/C/D/E",
  "urgency": "紧急程度: 低/中/高/紧急",
  "analysis": "2-3句分析摘要",
  "suggestions": ["建议1", "建议2", "建议3"]
}}"""

    content = _request(cfg, [{'role': 'user', 'content': prompt}])
    if isinstance(content, dict):
        return content

    if content.startswith('```'):
        content = content.split('\n', 1)[-1]
    if content.endswith('```'):
        content = content.rsplit('```', 1)[0]
    content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {'error': 'AI 返回格式异常'}

    for key in ('rating', 'urgency', 'analysis', 'suggestions'):
        if key not in result:
            return {'error': f'AI 返回缺少字段: {key}'}
    return result


def chat(record, history: list) -> dict:
    """多轮对话追问，history 为 [{'role':'user','content':'...'}, ...]"""
    cfg = load_config()
    if not cfg.get('api_key'):
        return {'error': '未配置 API Key'}

    summary = _record_summary(record)
    system = {
        'role': 'system',
        'content': f'你是一位道路工程专家AI助手，正在协助用户分析道路缺陷检测数据。以下是当前检测记录:\n{summary}\n\n请用中文简洁回答用户的问题。'
    }
    messages = [system] + history
    content = _request(cfg, messages)
    if isinstance(content, dict):
        return content
    return {'content': content}
