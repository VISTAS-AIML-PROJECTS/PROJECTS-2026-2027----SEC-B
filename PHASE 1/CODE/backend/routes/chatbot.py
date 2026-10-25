from flask import Blueprint, request, jsonify
from services.chatbot import chat

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('', methods=['POST'])
def handle_chat():
    data = request.get_json(force=True)
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({'error': 'No message provided.'}), 400

    result = chat(message, history)
    return jsonify(result)
