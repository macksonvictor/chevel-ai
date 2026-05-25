#include <algorithm>
#include <cctype>
#include <cmath>
#include <iostream>
#include <regex>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

std::string trim(const std::string& value) {
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char ch) {
        return std::isspace(ch);
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char ch) {
        return std::isspace(ch);
    }).base();
    if (begin >= end) {
        return "";
    }
    return std::string(begin, end);
}

std::string lower_ascii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return value;
}

bool starts_with(const std::string& value, const std::string& prefix) {
    return value.rfind(prefix, 0) == 0;
}

std::string after_prefix(const std::string& value, const std::vector<std::string>& prefixes) {
    for (const auto& prefix : prefixes) {
        if (starts_with(value, prefix)) {
            return trim(value.substr(prefix.size()));
        }
    }
    return "";
}

std::string after_prefix_preserve(
    const std::string& lower_value,
    const std::string& original_value,
    const std::vector<std::string>& prefixes
) {
    for (const auto& prefix : prefixes) {
        if (starts_with(lower_value, prefix)) {
            return trim(original_value.substr(prefix.size()));
        }
    }
    return "";
}

std::string join_args(int argc, char** argv, int start) {
    std::string result;
    for (int i = start; i < argc; ++i) {
        if (!result.empty()) {
            result += " ";
        }
        result += argv[i];
    }
    return result;
}

std::string escape_json(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (const auto ch : value) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out += ch; break;
        }
    }
    return out;
}

std::unordered_map<std::string, std::vector<std::string>> allowed_programs() {
    return {
        {"calculadora", {"calc.exe"}},
        {"calc", {"calc.exe"}},
        {"bloco de notas", {"notepad.exe"}},
        {"notepad", {"notepad.exe"}},
        {"explorador", {"explorer.exe"}},
        {"explorer", {"explorer.exe"}},
    };
}

void emit_action(const std::string& action, const std::string& key, const std::string& value, double confidence) {
    std::cout
        << "{\"matched\":true,\"tipo\":\"acao\",\"acao\":\"" << action
        << "\",\"parametros\":{\"" << key << "\":\"" << escape_json(value)
        << "\"},\"confianca\":" << confidence
        << ",\"engine\":\"cpp-service\"}";
}

void emit_light_action(const std::string& action, const std::string& local, double confidence) {
    std::cout
        << "{\"matched\":true,\"tipo\":\"acao\",\"acao\":\"controlar_luz\""
        << ",\"parametros\":{\"acao\":\"" << action << "\"";
    if (!local.empty()) {
        std::cout << ",\"local\":\"" << escape_json(local) << "\"";
    }
    std::cout << "},\"confianca\":" << confidence << ",\"engine\":\"cpp-service\"}";
}

int detect_intent(const std::string& message) {
    const auto original = trim(message);
    const auto text = lower_ascii(original);
    if (text.empty()) {
        std::cout << "{\"matched\":false,\"engine\":\"cpp-service\"}";
        return 0;
    }

    std::string value = after_prefix_preserve(text, original, {
        "busque o arquivo ",
        "buscar o arquivo ",
        "procure o arquivo ",
        "procurar o arquivo ",
        "encontre o arquivo ",
        "busque arquivo ",
        "buscar arquivo ",
        "procure arquivo ",
        "procurar arquivo ",
        "encontre arquivo ",
        "busque ",
        "buscar ",
        "procure ",
        "procurar ",
        "encontre ",
        "encontrar ",
    });
    if (!value.empty()) {
        emit_action("buscar_arquivo", "nome", value, 0.96);
        return 0;
    }

    value = after_prefix_preserve(text, original, {
        "abra o arquivo ",
        "abrir o arquivo ",
        "abre o arquivo ",
        "acesse o arquivo ",
        "acessar o arquivo ",
        "abra arquivo ",
        "abrir arquivo ",
        "abre arquivo ",
        "acesse arquivo ",
        "acessar arquivo ",
        "abra a pasta ",
        "abrir a pasta ",
        "abra pasta ",
        "abrir pasta ",
    });
    if (!value.empty()) {
        emit_action("abrir_arquivo", "caminho", value, 0.96);
        return 0;
    }

    value = after_prefix_preserve(text, original, {
        "execute programa ",
        "executar programa ",
        "executa programa ",
        "rode programa ",
        "rodar programa ",
        "abra o programa ",
        "abrir o programa ",
        "abra programa ",
        "abrir programa ",
        "abra ",
        "abrir ",
    });
    if (!value.empty()) {
        emit_action("executar_programa", "programa", value, 0.94);
        return 0;
    }

    value = after_prefix_preserve(text, original, {
        "enviar email para ",
        "envie email para ",
        "mandar email para ",
        "mande email para ",
    });
    if (!value.empty()) {
        emit_action("enviar_email", "destinatario", value, 0.9);
        return 0;
    }

    if (starts_with(text, "acenda") || starts_with(text, "ligue")) {
        std::string local = after_prefix(text, {"acenda a luz da ", "acenda a luz do ", "ligue a luz da ", "ligue a luz do "});
        emit_light_action("on", local, 0.88);
        return 0;
    }
    if (starts_with(text, "apague") || starts_with(text, "desligue")) {
        std::string local = after_prefix(text, {"apague a luz da ", "apague a luz do ", "desligue a luz da ", "desligue a luz do "});
        emit_light_action("off", local, 0.88);
        return 0;
    }

    std::cout << "{\"matched\":false,\"engine\":\"cpp-service\"}";
    return 0;
}

int validate_program(const std::string& program) {
    const auto key = lower_ascii(trim(program));
    if (key.find('&') != std::string::npos ||
        key.find('|') != std::string::npos ||
        key.find(';') != std::string::npos ||
        key.find('<') != std::string::npos ||
        key.find('>') != std::string::npos ||
        key.find('`') != std::string::npos) {
        std::cout << "{\"ok\":false,\"error\":\"Comandos de shell nao sao permitidos no MVP.\"}";
        return 0;
    }

    const auto programs = allowed_programs();
    const auto found = programs.find(key);
    if (found == programs.end()) {
        std::cout << "{\"ok\":false,\"error\":\"Programa nao permitido no dominio C++.\"}";
        return 0;
    }

    std::cout << "{\"ok\":true,\"command\":[";
    for (std::size_t i = 0; i < found->second.size(); ++i) {
        if (i > 0) {
            std::cout << ",";
        }
        std::cout << "\"" << escape_json(found->second[i]) << "\"";
    }
    std::cout << "]}";
    return 0;
}

bool contains_shell_meta(const std::string& value) {
    return value.find('&') != std::string::npos ||
        value.find('|') != std::string::npos ||
        value.find(';') != std::string::npos ||
        value.find('<') != std::string::npos ||
        value.find('>') != std::string::npos ||
        value.find('`') != std::string::npos;
}

int assess_risk(const std::string& action, const std::string& parameters_json) {
    const auto key = lower_ascii(trim(action));
    std::string risk = "medio";
    bool requires_confirmation = true;
    std::string reason = "acao desconhecida";

    if (key == "buscar_arquivo") {
        risk = "seguro";
        requires_confirmation = false;
        reason = "busca local limitada";
    } else if (key == "abrir_arquivo" || key == "controlar_luz") {
        risk = "baixo";
        requires_confirmation = false;
        reason = "acao local reversivel ou stub";
    } else if (key == "executar_programa") {
        if (contains_shell_meta(parameters_json)) {
            risk = "critico";
            requires_confirmation = true;
            reason = "metacaracter de shell detectado";
        } else {
            risk = "baixo";
            requires_confirmation = false;
            reason = "programa ainda sera validado por allowlist";
        }
    } else if (key == "enviar_email" || key == "mover_braco") {
        risk = "alto";
        requires_confirmation = true;
        reason = "acao externa ou fisica requer confirmacao no MVP";
    }

    std::cout
        << "{\"ok\":true,\"risk\":\"" << risk
        << "\",\"requires_confirmation\":" << (requires_confirmation ? "true" : "false")
        << ",\"reason\":\"" << escape_json(reason)
        << "\",\"engine\":\"cpp-service\"}";
    return 0;
}

double number_value(const std::string& json, const std::string& key, double fallback) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*(-?[0-9]+(?:\\.[0-9]+)?)");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        try {
            return std::stod(match[1].str());
        } catch (...) {
            return fallback;
        }
    }
    return fallback;
}

bool bool_value(const std::string& json, const std::string& key, bool fallback) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*(true|false)");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return match[1].str() == "true";
    }
    return fallback;
}

bool has_key(const std::string& json, const std::string& key) {
    return json.find("\"" + key + "\"") != std::string::npos;
}

void emit_reflex_item(
    bool& first,
    const std::string& nome,
    const std::string& descricao,
    int prioridade,
    const std::string& tipo,
    const std::string& motivo
) {
    if (!first) {
        std::cout << ",";
    }
    first = false;
    std::cout
        << "{\"nome\":\"" << escape_json(nome)
        << "\",\"descricao\":\"" << escape_json(descricao)
        << "\",\"prioridade\":" << prioridade
        << ",\"acao\":{\"tipo\":\"" << escape_json(tipo)
        << "\",\"motivo\":\"" << escape_json(motivo)
        << "\"},\"engine\":\"cpp-service\"}";
}

int evaluate_reflexes(const std::string& sensor_json) {
    std::cout << "{\"ok\":true,\"reflexes\":[";
    bool first = true;

    if (bool_value(sensor_json, "pessoa_detectada_zona_braco", false)) {
        emit_reflex_item(first, "pessoa_zona_braco", "Pessoa detectada na zona do braco", 100, "parada_emergencia", "pessoa_zona_braco");
    }
    if (number_value(sensor_json, "temp_motor_max", 0.0) > 80.0) {
        emit_reflex_item(first, "temp_motor_alta", "Temperatura do motor acima de 80C", 95, "desligar_motor", "temperatura");
    }
    if (number_value(sensor_json, "bateria", 100.0) < 10.0) {
        emit_reflex_item(first, "bateria_baixa", "Bateria abaixo de 10%", 90, "parada_emergencia", "bateria_baixa");
    }
    if (number_value(sensor_json, "corrente_motor_max", 0.0) > 4.0) {
        emit_reflex_item(first, "sobrecorrente_motor", "Sobrecorrente acima de 4A", 85, "reduzir_potencia", "sobrecorrente");
    }
    if (has_key(sensor_json, "pressao_garra") && number_value(sensor_json, "pressao_garra", 1.0) < 0.3) {
        emit_reflex_item(first, "pressao_garra_baixa", "Pressao da garra abaixo de 30%", 75, "apertar_garra", "pressao_baixa");
    }

    std::cout << "]}";
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "{\"ok\":false,\"error\":\"missing command\"}";
        return 1;
    }

    const std::string command = argv[1];
    if (command == "version") {
        std::cout << "{\"ok\":true,\"version\":\"chevel_core_cpp/0.2.0\"}";
        return 0;
    }
    if (command == "detect") {
        return detect_intent(join_args(argc, argv, 2));
    }
    if (command == "program") {
        return validate_program(join_args(argc, argv, 2));
    }
    if (command == "risk") {
        if (argc < 3) {
            std::cout << "{\"ok\":false,\"error\":\"risk requires action\"}";
            return 1;
        }
        const std::string action = argv[2];
        const std::string payload = join_args(argc, argv, 3);
        return assess_risk(action, payload);
    }
    if (command == "reflex") {
        return evaluate_reflexes(join_args(argc, argv, 2));
    }

    std::cout << "{\"ok\":false,\"error\":\"unknown command\"}";
    return 1;
}
