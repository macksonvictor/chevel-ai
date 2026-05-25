const messagesEl = document.getElementById("messages");
const appShellEl = document.querySelector(".app-shell");
const formEl = document.getElementById("messageForm");
const inputEl = document.getElementById("messageInput");
const sendButtonEl = document.getElementById("sendButton");
const typingEl = document.getElementById("typingIndicator");
const connectionStatusEl = document.getElementById("connectionStatus");
const runtimeStatusEl = document.getElementById("runtimeStatus");
const modelStatusEl = document.getElementById("modelStatus");
const heroLogoEl = document.getElementById("heroLogo");
const sidebarButtonEl = document.getElementById("sidebarButton");
const newChatButtonEl = document.getElementById("newChatButton");
const sidebarNewChatButtonEl = document.getElementById("sidebarNewChatButton");
const launchButtonEl = document.getElementById("launchButton");
const voiceButtonEl = document.getElementById("voiceButton");
const settingsButtonEl = document.getElementById("settingsButton");
const attachButtonEl = document.getElementById("attachButton");
const webSearchButtonEl = document.getElementById("webSearchButton");
const fileInputEl = document.getElementById("fileInput");
const attachmentStatusEl = document.getElementById("attachmentStatus");
const voiceStatusEl = document.getElementById("voiceStatus");
const historySidebarEl = document.getElementById("historySidebar");
const historyListEl = document.getElementById("historyList");

const MODEL_NAME = "HELI 1.5";
const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
const MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024;
const MAX_TEXT_ATTACHMENT_CHARS = 12000;

let webSearchEnabled = false;
let attachedFiles = [];
let voiceEnabled = false;
let recognition = null;
let recognitionActive = false;
let voiceBusy = false;
let voiceRestartBlocked = false;
let lastVoiceError = "";
let voiceStatusTimer = null;

function addMessage(role, text, attachments = []) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    if (role === "system") {
        wrapper.textContent = text;
    } else {
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;

        if (attachments.length > 0) {
            bubble.appendChild(renderAttachmentChips(attachments));
        }

        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = role === "user" ? "Voce" : "chevel";

        wrapper.appendChild(bubble);
        wrapper.appendChild(meta);
    }

    messagesEl.appendChild(wrapper);
    updateHeroVisibility();
    updateHistory();
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderAttachmentChips(attachments) {
    const list = document.createElement("div");
    list.className = "attachment-chips";
    attachments.forEach((item) => {
        const chip = document.createElement("span");
        chip.className = `attachment-chip ${item.kind || "file"}`;
        const label = item.kind === "image" ? "imagem" : item.kind === "audio" ? "audio" : "arquivo";
        chip.textContent = `${label}: ${item.name}`;
        list.appendChild(chip);
    });
    return list;
}

function showTyping() {
    typingEl.classList.add("active");
    formEl.classList.add("loading");
}

function hideTyping() {
    typingEl.classList.remove("active");
    formEl.classList.remove("loading");
}

function updateHeroVisibility() {
    const hasConversation = messagesEl.querySelectorAll(".message:not(.system)").length > 0;
    heroLogoEl.classList.toggle("hidden", hasConversation);
    appShellEl.classList.toggle("has-conversation", hasConversation);
}

function clearChat() {
    messagesEl.querySelectorAll(".message:not(.system)").forEach((message) => message.remove());
    hideTyping();
    sendButtonEl.disabled = false;
    inputEl.value = "";
    clearAttachments();
    updateHeroVisibility();
    updateHistory();
    inputEl.focus();
}

function toggleSidebar(forceOpen) {
    const shouldOpen = typeof forceOpen === "boolean"
        ? forceOpen
        : !historySidebarEl.classList.contains("active");

    historySidebarEl.classList.toggle("active", shouldOpen);
    appShellEl.classList.toggle("sidebar-open", shouldOpen);
    sidebarButtonEl.classList.toggle("active", shouldOpen);
    sidebarButtonEl.setAttribute("aria-expanded", String(shouldOpen));
}

function setWebSearchEnabled(nextValue) {
    webSearchEnabled = nextValue;
    webSearchButtonEl.classList.toggle("active", webSearchEnabled);
    webSearchButtonEl.setAttribute("aria-pressed", String(webSearchEnabled));
    webSearchButtonEl.title = webSearchEnabled ? "Pesquisa web ativada" : "Pesquisa web";
}

function updateAttachmentStatus() {
    if (attachedFiles.length === 0) {
        attachmentStatusEl.textContent = "";
        attachmentStatusEl.classList.remove("visible");
        return;
    }

    attachmentStatusEl.textContent = attachedFiles
        .map((file) => `${file.kind === "image" ? "imagem" : file.kind === "audio" ? "audio" : "arquivo"}: ${file.name}`)
        .join(", ");
    attachmentStatusEl.classList.add("visible");
}

function clearAttachments() {
    attachedFiles = [];
    fileInputEl.value = "";
    updateAttachmentStatus();
}

function getDisplayMessage(text) {
    const tags = [];
    if (webSearchEnabled) {
        tags.push("web");
    }
    if (attachedFiles.length > 0) {
        tags.push(`${attachedFiles.length} midia/anexo(s)`);
    }
    return tags.length > 0 ? `${text}\n${tags.map((tag) => `[${tag}]`).join(" ")}` : text;
}

async function sendMessageToModel(message) {
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message,
            model: MODEL_NAME,
            use_web: webSearchEnabled,
            attachments: attachedFiles.map((file) => ({
                name: file.name,
                size: file.size,
                type: file.type,
                kind: file.kind,
                data_url: file.data_url,
                text: file.text,
            })),
        }),
    });

    if (!response.ok) {
        throw new Error(`Falha ao falar com chevel (${response.status})`);
    }

    return response.json();
}

async function handleMessageSubmit(event) {
    event.preventDefault();

    let userText = inputEl.value.trim();
    if (!userText && attachedFiles.length > 0) {
        userText = "Analise os anexos enviados.";
    }
    inputEl.value = "";
    await submitUserText(userText);
}

async function submitUserText(userText) {
    if (!userText || sendButtonEl.disabled) {
        return;
    }

    addMessage("user", getDisplayMessage(userText), attachedFiles);
    showTyping();
    sendButtonEl.disabled = true;

    try {
        const data = await sendMessageToModel(userText);
        const answer = data.response || data.text || "chevel respondeu sem conteudo.";
        addMessage("assistant", answer);
        speakResponse(answer);
    } catch (error) {
        addMessage("assistant", error.message || "Erro ao enviar mensagem para o modelo.");
    } finally {
        hideTyping();
        sendButtonEl.disabled = false;
        clearAttachments();
        inputEl.focus();
        restartVoiceListeningSoon();
    }
}

function voiceSupported() {
    return Boolean(SpeechRecognitionCtor) && "speechSynthesis" in window;
}

function setVoiceUi(enabled) {
    launchButtonEl.classList.toggle("active", enabled);
    launchButtonEl.setAttribute("aria-pressed", String(enabled));
    launchButtonEl.title = enabled ? "Voz ativada: escutando pelo microfone" : "Ativar voz";
    voiceButtonEl.classList.toggle("active", enabled);
    voiceButtonEl.setAttribute("aria-pressed", String(enabled));
    voiceButtonEl.title = enabled ? "Voz ativada: escutando pelo microfone" : "Ativar voz";
}

function showVoiceStatus(message, isError = false, timeout = 4200) {
    if (!voiceStatusEl) {
        return;
    }
    window.clearTimeout(voiceStatusTimer);
    voiceStatusEl.textContent = message;
    voiceStatusEl.classList.toggle("error", isError);
    voiceStatusEl.classList.add("visible");
    if (timeout > 0) {
        voiceStatusTimer = window.setTimeout(() => {
            voiceStatusEl.classList.remove("visible", "error");
            voiceStatusEl.textContent = "";
        }, timeout);
    }
}

function voiceErrorMessage(errorName) {
    const messages = {
        network: "Escuta indisponivel neste navegador. Verifique internet/permissao do microfone.",
        "not-allowed": "Microfone bloqueado pelo navegador.",
        "service-not-allowed": "Servico de voz bloqueado pelo navegador.",
        "audio-capture": "Microfone nao encontrado ou ocupado.",
        aborted: "Escuta interrompida.",
        "no-speech": "Nao ouvi nada. Tente falar mais perto do microfone.",
    };
    return messages[errorName] || `Escuta indisponivel: ${errorName}`;
}

function disableVoiceAfterError(errorName) {
    voiceEnabled = false;
    voiceRestartBlocked = true;
    recognitionActive = false;
    setVoiceUi(false);
    showVoiceStatus(voiceErrorMessage(errorName), true, 7000);
}

function ensureRecognition() {
    if (recognition || !SpeechRecognitionCtor) {
        return recognition;
    }

    recognition = new SpeechRecognitionCtor();
    recognition.lang = "pt-BR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        recognitionActive = true;
        launchButtonEl.classList.add("listening");
        voiceButtonEl.classList.add("listening");
    };

    recognition.onend = () => {
        recognitionActive = false;
        launchButtonEl.classList.remove("listening");
        voiceButtonEl.classList.remove("listening");
        if (voiceRestartBlocked) {
            return;
        }
        restartVoiceListeningSoon();
    };

    recognition.onerror = (event) => {
        recognitionActive = false;
        const errorName = event.error || "unknown";
        if (errorName === "no-speech") {
            showVoiceStatus(voiceErrorMessage(errorName), false, 2400);
            return;
        }
        if (["network", "not-allowed", "service-not-allowed", "audio-capture"].includes(errorName)) {
            disableVoiceAfterError(errorName);
            return;
        }
        if (lastVoiceError !== errorName) {
            lastVoiceError = errorName;
            showVoiceStatus(voiceErrorMessage(errorName), true, 5200);
        }
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map((result) => result[0]?.transcript || "")
            .join(" ")
            .trim();
        if (transcript) {
            stopVoiceListening();
            submitUserText(transcript);
        }
    };

    return recognition;
}

function toggleVoiceMode() {
    if (!voiceSupported()) {
        showVoiceStatus("Seu navegador nao liberou fala/escuta para este chat.", true, 6500);
        return;
    }

    voiceEnabled = !voiceEnabled;
    voiceRestartBlocked = false;
    lastVoiceError = "";
    setVoiceUi(voiceEnabled);

    if (voiceEnabled) {
        showVoiceStatus("Voz ativa. Fale pelo microfone.", false, 3800);
        startVoiceListening();
    } else {
        voiceRestartBlocked = true;
        window.speechSynthesis.cancel();
        stopVoiceListening();
        showVoiceStatus("Voz desativada.", false, 2200);
    }
}

function startVoiceListening() {
    if (!voiceEnabled || voiceRestartBlocked || voiceBusy || recognitionActive || sendButtonEl.disabled) {
        return;
    }
    const instance = ensureRecognition();
    if (!instance) {
        return;
    }
    try {
        instance.start();
    } catch {
        recognitionActive = false;
        showVoiceStatus("Escuta ja estava iniciando.", false, 1800);
    }
}

function stopVoiceListening() {
    if (recognition && recognitionActive) {
        try {
            recognition.stop();
        } catch {
            recognitionActive = false;
        }
    }
}

function restartVoiceListeningSoon() {
    if (!voiceEnabled || voiceRestartBlocked || voiceBusy || sendButtonEl.disabled) {
        return;
    }
    window.setTimeout(startVoiceListening, 450);
}

function speakResponse(text) {
    if (!voiceEnabled || !("speechSynthesis" in window)) {
        return;
    }
    voiceBusy = true;
    stopVoiceListening();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pt-BR";
    utterance.rate = 1;
    utterance.volume = 1;
    utterance.onend = () => {
        voiceBusy = false;
        restartVoiceListeningSoon();
    };
    utterance.onerror = () => {
        voiceBusy = false;
        restartVoiceListeningSoon();
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

function attachmentKind(file) {
    if (file.type.startsWith("image/")) {
        return "image";
    }
    if (file.type.startsWith("audio/")) {
        return "audio";
    }
    if (file.type.startsWith("text/") || /\.(txt|md|json|csv|log)$/i.test(file.name)) {
        return "text";
    }
    return "file";
}

function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
    });
}

async function normalizeAttachment(file) {
    const kind = attachmentKind(file);
    const base = {
        name: file.name,
        size: file.size,
        type: file.type || "application/octet-stream",
        kind,
    };

    if (file.size > MAX_ATTACHMENT_BYTES) {
        return {
            ...base,
            skipped: true,
            reason: "Arquivo acima do limite de 8 MB para este MVP.",
        };
    }

    if (kind === "image" || kind === "audio") {
        return {
            ...base,
            data_url: await readFileAsDataUrl(file),
        };
    }

    if (kind === "text") {
        const text = await readFileAsText(file);
        return {
            ...base,
            text: text.slice(0, MAX_TEXT_ATTACHMENT_CHARS),
        };
    }

    return base;
}

function updateHistory() {
    const visibleMessages = Array.from(messagesEl.querySelectorAll(".message:not(.system) .bubble"))
        .map((bubble) => bubble.textContent.trim())
        .filter(Boolean)
        .slice(-8)
        .reverse();

    historyListEl.replaceChildren();

    if (visibleMessages.length === 0) {
        const empty = document.createElement("div");
        empty.className = "drawer-empty";
        empty.textContent = "Nenhuma conversa nesta sessao.";
        historyListEl.appendChild(empty);
        return;
    }

    visibleMessages.forEach((message) => {
        const item = document.createElement("div");
        item.className = "drawer-item";
        item.textContent = message;
        historyListEl.appendChild(item);
    });
}

async function refreshHealth() {
    try {
        const response = await fetch("/health");
        const data = await response.json();
        const ollama = data?.system?.ollama;
        const engineModel = ollama?.active_model;

        modelStatusEl.textContent = MODEL_NAME;
        modelStatusEl.title = engineModel ? `Motor local temporario: ${engineModel}` : MODEL_NAME;
        connectionStatusEl.textContent = "Conectado";
        runtimeStatusEl.textContent = ollama?.online ? "chevel pronto" : "chevel sem Ollama";
        runtimeStatusEl.style.color = ollama?.online ? "var(--active)" : "var(--danger)";
    } catch {
        modelStatusEl.textContent = "health indisponivel";
        connectionStatusEl.textContent = "Erro de conexao";
    }
}

formEl.addEventListener("submit", handleMessageSubmit);

sidebarButtonEl.addEventListener("click", () => {
    toggleSidebar();
});

newChatButtonEl.addEventListener("click", clearChat);
sidebarNewChatButtonEl.addEventListener("click", () => {
    clearChat();
    toggleSidebar(false);
});

attachButtonEl.addEventListener("click", () => {
    fileInputEl.click();
});

fileInputEl.addEventListener("change", () => {
    const selected = Array.from(fileInputEl.files || []);
    if (selected.length === 0) {
        clearAttachments();
        inputEl.focus();
        return;
    }
    attachmentStatusEl.textContent = "Preparando anexos...";
    attachmentStatusEl.classList.add("visible");
    Promise.all(selected.slice(0, 6).map(normalizeAttachment))
        .then((items) => {
            const skipped = items.filter((item) => item.skipped);
            attachedFiles = items.filter((item) => !item.skipped);
            updateAttachmentStatus();
            if (skipped.length > 0) {
                addMessage("assistant", skipped.map((item) => `${item.name}: ${item.reason}`).join("\n"));
            }
            inputEl.focus();
        })
        .catch((error) => {
            addMessage("assistant", error.message || "Nao consegui preparar o anexo.");
            clearAttachments();
            inputEl.focus();
        });
});

webSearchButtonEl.addEventListener("click", () => {
    setWebSearchEnabled(!webSearchEnabled);
    inputEl.focus();
});

launchButtonEl.addEventListener("click", () => {
    toggleVoiceMode();
    toggleSidebar(false);
});

voiceButtonEl.addEventListener("click", () => {
    toggleVoiceMode();
    inputEl.focus();
});

settingsButtonEl.addEventListener("click", () => {
    addMessage("assistant", `Modelo ativo: ${MODEL_NAME}\nMotor temporario: Ollama local.\nImagem/audio: entrada aceita pela interface; analise profunda entra quando o backend multimodal HELI estiver conectado.`);
    toggleSidebar(false);
});

document.addEventListener("pointerdown", (event) => {
    if (!historySidebarEl.classList.contains("active")) {
        return;
    }
    if (historySidebarEl.contains(event.target) || sidebarButtonEl.contains(event.target)) {
        return;
    }
    toggleSidebar(false);
});

window.addEventListener("load", () => {
    refreshHealth();
    updateHistory();
    inputEl.focus();
});
