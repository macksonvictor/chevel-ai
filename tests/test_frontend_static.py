from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1] / "interfaces" / "chat" / "web"


def test_mic_button_is_next_to_send_button():
    index = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert index.index('id="modelStatus"') < index.index('id="voiceButton"') < index.index('id="sendButton"')


def test_messages_have_real_composer_clearance():
    css = (WEB_ROOT / "static" / "styles.css").read_text(encoding="utf-8")

    assert "bottom: calc(var(--composer-bottom) + var(--composer-height) + var(--conversation-gap));" in css
    assert ".app-shell.has-conversation .typing" in css


def test_voice_network_errors_do_not_create_chat_bubbles():
    js = (WEB_ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "disableVoiceAfterError" in js
    assert 'addMessage("assistant", `Voz:' not in js
