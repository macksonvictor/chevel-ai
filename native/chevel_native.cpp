#include <cmath>
#include <algorithm>
#include <cctype>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

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

py::dict make_action(
    const std::string& action,
    const py::dict& params,
    double confidence
) {
    py::dict result;
    result["matched"] = true;
    result["tipo"] = "acao";
    result["acao"] = action;
    result["parametros"] = params;
    result["confianca"] = confidence;
    result["engine"] = "cpp";
    return result;
}

py::dict no_action() {
    py::dict result;
    result["matched"] = false;
    result["engine"] = "cpp";
    return result;
}

std::string light_local(const std::string& text) {
    return after_prefix(text, {
        "acenda a luz da ",
        "acenda a luz do ",
        "ligue a luz da ",
        "ligue a luz do ",
        "apague a luz da ",
        "apague a luz do ",
        "desligue a luz da ",
        "desligue a luz do ",
    });
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

py::dict detect_intent(const std::string& message) {
    const auto original = trim(message);
    const auto text = lower_ascii(original);
    if (text.empty()) {
        return no_action();
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
        py::dict params;
        params["nome"] = value;
        return make_action("buscar_arquivo", params, 0.96);
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
        py::dict params;
        params["caminho"] = value;
        return make_action("abrir_arquivo", params, 0.96);
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
        py::dict params;
        params["programa"] = value;
        return make_action("executar_programa", params, 0.94);
    }

    value = after_prefix_preserve(text, original, {
        "enviar email para ",
        "envie email para ",
        "mandar email para ",
        "mande email para ",
    });
    if (!value.empty()) {
        py::dict params;
        params["destinatario"] = value;
        return make_action("enviar_email", params, 0.9);
    }

    if (starts_with(text, "acenda") || starts_with(text, "ligue")) {
        py::dict params;
        params["acao"] = "on";
        const auto local = light_local(text);
        if (!local.empty()) {
            params["local"] = local;
        }
        return make_action("controlar_luz", params, 0.88);
    }
    if (starts_with(text, "apague") || starts_with(text, "desligue")) {
        py::dict params;
        params["acao"] = "off";
        const auto local = light_local(text);
        if (!local.empty()) {
            params["local"] = local;
        }
        return make_action("controlar_luz", params, 0.88);
    }

    if (text.find("braco") != std::string::npos || text.find("bra") != std::string::npos) {
        if (text.find("mova") != std::string::npos || text.find("mover") != std::string::npos) {
            py::dict params;
            params["instrucao"] = text;
            return make_action("mover_braco", params, 0.84);
        }
    }

    return no_action();
}

std::vector<std::string> allowed_program_command(const std::string& program) {
    const auto key = lower_ascii(trim(program));
    if (key.find('&') != std::string::npos ||
        key.find('|') != std::string::npos ||
        key.find(';') != std::string::npos ||
        key.find('<') != std::string::npos ||
        key.find('>') != std::string::npos ||
        key.find('`') != std::string::npos) {
        throw std::invalid_argument("Comandos de shell nao sao permitidos no MVP.");
    }

    const auto programs = allowed_programs();
    const auto found = programs.find(key);
    if (found == programs.end()) {
        throw std::invalid_argument("Programa nao permitido no dominio C++.");
    }
    return found->second;
}

std::vector<std::string> known_programs() {
    std::vector<std::string> keys;
    for (const auto& item : allowed_programs()) {
        keys.push_back(item.first);
    }
    std::sort(keys.begin(), keys.end());
    return keys;
}

bool contains_shell_meta(const std::string& value) {
    return value.find('&') != std::string::npos ||
        value.find('|') != std::string::npos ||
        value.find(';') != std::string::npos ||
        value.find('<') != std::string::npos ||
        value.find('>') != std::string::npos ||
        value.find('`') != std::string::npos;
}

py::dict assess_action_risk(const std::string& action, const py::dict& parameters) {
    const auto key = lower_ascii(trim(action));
    py::dict result;
    result["ok"] = true;
    result["engine"] = "cpp";

    std::string risk = "medio";
    bool confirmation = true;
    std::string reason = "acao desconhecida";

    if (key == "buscar_arquivo") {
        risk = "seguro";
        confirmation = false;
        reason = "busca local limitada";
    } else if (key == "abrir_arquivo" || key == "controlar_luz") {
        risk = "baixo";
        confirmation = false;
        reason = "acao local reversivel ou stub";
    } else if (key == "executar_programa") {
        std::string program;
        if (parameters.contains("programa")) {
            program = py::str(parameters["programa"]);
        }
        if (contains_shell_meta(program)) {
            risk = "critico";
            confirmation = true;
            reason = "metacaracter de shell detectado";
        } else {
            risk = "baixo";
            confirmation = false;
            reason = "programa ainda sera validado por allowlist";
        }
    } else if (key == "enviar_email" || key == "mover_braco") {
        risk = "alto";
        confirmation = true;
        reason = "acao externa ou fisica requer confirmacao no MVP";
    }

    result["risk"] = risk;
    result["requires_confirmation"] = confirmation;
    result["reason"] = reason;
    return result;
}

double dict_number(const py::dict& values, const char* key, double fallback) {
    if (!values.contains(key) || values[key].is_none()) {
        return fallback;
    }
    try {
        return py::cast<double>(values[key]);
    } catch (...) {
        return fallback;
    }
}

bool dict_bool(const py::dict& values, const char* key, bool fallback) {
    if (!values.contains(key) || values[key].is_none()) {
        return fallback;
    }
    try {
        return py::cast<bool>(values[key]);
    } catch (...) {
        return fallback;
    }
}

py::dict make_reflex(
    const std::string& nome,
    const std::string& descricao,
    int prioridade,
    const std::string& tipo,
    const std::string& motivo
) {
    py::dict action;
    action["tipo"] = tipo;
    action["motivo"] = motivo;

    py::dict result;
    result["nome"] = nome;
    result["descricao"] = descricao;
    result["prioridade"] = prioridade;
    result["acao"] = action;
    result["engine"] = "cpp";
    return result;
}

py::list evaluate_reflexes(const py::dict& sensor_state) {
    py::list reflexes;
    if (dict_bool(sensor_state, "pessoa_detectada_zona_braco", false)) {
        reflexes.append(make_reflex("pessoa_zona_braco", "Pessoa detectada na zona do braco", 100, "parada_emergencia", "pessoa_zona_braco"));
    }
    if (dict_number(sensor_state, "temp_motor_max", 0.0) > 80.0) {
        reflexes.append(make_reflex("temp_motor_alta", "Temperatura do motor acima de 80C", 95, "desligar_motor", "temperatura"));
    }
    if (dict_number(sensor_state, "bateria", 100.0) < 10.0) {
        reflexes.append(make_reflex("bateria_baixa", "Bateria abaixo de 10%", 90, "parada_emergencia", "bateria_baixa"));
    }
    if (dict_number(sensor_state, "corrente_motor_max", 0.0) > 4.0) {
        reflexes.append(make_reflex("sobrecorrente_motor", "Sobrecorrente acima de 4A", 85, "reduzir_potencia", "sobrecorrente"));
    }
    if (sensor_state.contains("pressao_garra") && dict_number(sensor_state, "pressao_garra", 1.0) < 0.3) {
        reflexes.append(make_reflex("pressao_garra_baixa", "Pressao da garra abaixo de 30%", 75, "apertar_garra", "pressao_baixa"));
    }
    return reflexes;
}

double cosine_similarity(
    const std::vector<double>& query,
    const std::vector<double>& vector
) {
    if (query.size() != vector.size()) {
        throw std::invalid_argument("Vectors must have the same size.");
    }

    double dot = 0.0;
    double query_norm = 0.0;
    double vector_norm = 0.0;

    for (std::size_t i = 0; i < query.size(); ++i) {
        dot += query[i] * vector[i];
        query_norm += query[i] * query[i];
        vector_norm += vector[i] * vector[i];
    }

    if (query_norm == 0.0 || vector_norm == 0.0) {
        return 0.0;
    }

    return dot / (std::sqrt(query_norm) * std::sqrt(vector_norm));
}

std::vector<double> cosine_similarity_batch(
    const std::vector<double>& query,
    const std::vector<std::vector<double>>& vectors
) {
    std::vector<double> scores;
    scores.reserve(vectors.size());

    for (const auto& vector : vectors) {
        scores.push_back(cosine_similarity(query, vector));
    }

    return scores;
}

std::string version() {
    return std::string("chevel_native/") + CHEVEL_NATIVE_VERSION;
}

}  // namespace

PYBIND11_MODULE(chevel_native, module) {
    module.doc() = "Native C++ helpers for CHEVEL AI.";
    module.def("version", &version, "Return the native module version.");
    module.def("detect_intent", &detect_intent, "Detect a local action intent in C++.");
    module.def("allowed_program_command", &allowed_program_command, "Validate an allowlisted program in C++.");
    module.def("known_programs", &known_programs, "Return known allowlisted programs.");
    module.def("assess_action_risk", &assess_action_risk, "Classify action risk in C++.");
    module.def("evaluate_reflexes", &evaluate_reflexes, "Evaluate fast reflex rules in C++.");
    module.def(
        "cosine_similarity_batch",
        &cosine_similarity_batch,
        "Calculate cosine similarity for a query vector and a batch of vectors."
    );
}
