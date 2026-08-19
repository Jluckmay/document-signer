import hashlib
import io
import logging
import os
from datetime import datetime

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature, validate_pdf_timestamp
from pyhanko.sign.validation.pdf_embedded import collect_embedded_signatures

try:
    from pyhanko_certvalidator import ValidationContext
except ImportError:
    ValidationContext = None

try:
    from pyhanko.keys.pemder import load_certs_from_pemder
except ImportError:
    load_certs_from_pemder = None

LEGAL_NOTICE = (
    "Resultado técnico e informativo. Este verificador não substitui serviços oficiais, "
    "não certifica validade jurídica e não atribui efeitos legais ao documento."
)


class _HandledValidationWarning(logging.Filter):
    _PREFIXES = (
        "Failed to build path for ",
        "Error in diff operation between revision ",
    )

    def filter(self, record):
        return not record.getMessage().startswith(self._PREFIXES)


logging.getLogger("pyhanko.sign.validation.generic_cms").addFilter(
    _HandledValidationWarning()
)
logging.getLogger("pyhanko.sign.diff_analysis.policies").addFilter(
    _HandledValidationWarning()
)


def _safe_native(value):
    try:
        return value.native
    except Exception:
        return value


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value is not None else None


def _enum_name(value):
    if value is None:
        return None
    name = getattr(value, "name", None)
    if name:
        return str(name)
    text = str(value)
    return text.split(".")[-1] if "." in text else text


def _name_dict(name):
    try:
        native = name.native
        return native if isinstance(native, dict) else {"valor": str(native)}
    except Exception:
        return {"valor": str(name)}


def _common_name(name):
    data = _name_dict(name)
    value = data.get("common_name") or data.get("organization_name") or data.get("valor")
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value) if value else None


def _validity(cert):
    try:
        validity = cert["tbs_certificate"]["validity"]
        return {
            "inicio": _iso(_safe_native(validity["not_before"])),
            "fim": _iso(_safe_native(validity["not_after"])),
        }
    except Exception:
        return {"inicio": None, "fim": None}


def _fingerprint(cert):
    try:
        return hashlib.sha256(cert.dump()).hexdigest().upper()
    except Exception:
        return None


def identificar_infraestrutura(cert):
    subject = _name_dict(cert.subject)
    issuer = _name_dict(cert.issuer)
    texto = " ".join(str(value) for value in [subject, issuer]).lower()
    marcadores_gov_br = (
        "gov-br",
        "gov.br",
        "governo federal do brasil",
        "autoridade certificadora raiz do governo federal",
        "ac intermediaria do governo federal",
        "ac final do governo federal",
    )
    if any(marcador in texto for marcador in marcadores_gov_br):
        return {
            "nome": "Gov.br / Governo Federal do Brasil",
            "confianca_identificacao": "heuristica",
        }
    if "icp-brasil" in texto or "icp brasil" in texto:
        return {
            "nome": "ICP-Brasil",
            "confianca_identificacao": "heuristica",
        }
    if "icpedu" in texto or "icp-edu" in texto or "rede nacional de ensino e pesquisa" in texto:
        return {
            "nome": "ICPEdu / RNP",
            "confianca_identificacao": "heuristica",
        }
    if "eidas" in texto or "qualified" in texto or "qualified trust" in texto:
        return {
            "nome": "Possível infraestrutura europeia/eIDAS",
            "confianca_identificacao": "heuristica",
        }
    return {
        "nome": "Não identificada automaticamente",
        "confianca_identificacao": "indeterminada",
    }


def certificado_para_dict(cert):
    validity = _validity(cert)
    try:
        serial = str(cert.serial_number)
    except Exception:
        serial = None
    return {
        "titular": _common_name(cert.subject),
        "emissor": _common_name(cert.issuer),
        "subject": _name_dict(cert.subject),
        "issuer": _name_dict(cert.issuer),
        "numero_serie": serial,
        "valido_de": validity["inicio"],
        "valido_ate": validity["fim"],
        "sha256": _fingerprint(cert),
        "infraestrutura": identificar_infraestrutura(cert),
    }


def _trust_roots_from_env():
    raw = os.environ.get("VERIFIER_TRUST_ROOTS", "").strip()
    if not raw or load_certs_from_pemder is None:
        return []
    paths = [item.strip() for item in raw.split(os.pathsep) if item.strip()]
    existing = [path for path in paths if os.path.isfile(path)]
    if not existing:
        return []
    try:
        return list(load_certs_from_pemder(existing))
    except Exception:
        return []


def criar_contexto_validacao(allow_fetching=True, other_certs=None):
    if ValidationContext is None:
        return None
    kwargs = {
        "allow_fetching": bool(allow_fetching),
        "revocation_mode": "hard-fail" if allow_fetching else "none",
    }
    if other_certs:
        kwargs["other_certs"] = list(other_certs)
    extra_roots = _trust_roots_from_env()
    if extra_roots:
        kwargs["extra_trust_roots"] = extra_roots
    try:
        return ValidationContext(**kwargs)
    except Exception:
        return None


def _validation_path(status):
    path = getattr(status, "validation_path", None)
    if path is None:
        return []
    try:
        certs = list(path)
    except Exception:
        try:
            certs = list(path.iter_certs())
        except Exception:
            return []
    return [certificado_para_dict(cert) for cert in certs]


def _revocation(status, allow_fetching, context=None):
    details = getattr(status, "revocation_details", None)
    trusted = bool(getattr(status, "trusted", False))
    ocsp_count = 0
    crl_count = 0
    if context is not None:
        try:
            manager = context.revinfo_manager
            ocsp_count = len(manager.ocsps)
            crl_count = len(manager.crls)
        except Exception:
            pass
    evidence_found = (ocsp_count + crl_count) > 0
    revoked = (
        bool(getattr(status, "revoked", False))
        if details is not None
        else False
        if trusted and evidence_found
        else None
    )
    result = {
        "consultas_online_habilitadas": bool(allow_fetching),
        "consulta_realizada": bool(allow_fetching and evidence_found),
        "respostas_ocsp_obtidas": ocsp_count,
        "listas_crl_obtidas": crl_count,
        "revogado": revoked,
        "estado": (
            "revogado"
            if revoked is True
            else "nenhuma_revogacao_detectada"
            if revoked is False
            else "desabilitada"
            if not allow_fetching
            else "nao_consultada"
            if not evidence_found
            else "indeterminado"
        ),
        "conclusao": (
            "Foi detectada informação de revogação."
            if revoked is True
            else "Nenhuma revogação foi detectada nas evidências consultadas."
            if revoked is False
            else "As consultas online de revogação estão desabilitadas."
            if not allow_fetching
            else "Nenhuma resposta OCSP ou CRL foi obtida; a revogação não foi consultada."
            if not evidence_found
            else "Não foi possível obter evidência OCSP/CRL conclusiva em uma cadeia confiável; "
            "o estado de revogação é indeterminado."
        ),
    }
    if details is not None:
        result.update({
            "certificado_ca_revogado": bool(getattr(details, "ca_revoked", False)),
            "data_revogacao": _iso(getattr(details, "revocation_date", None)),
            "motivo": _enum_name(getattr(details, "revocation_reason", None)),
        })
    return result


def _timestamp_status(status):
    timestamp = getattr(status, "timestamp_validity", None)
    if timestamp is None:
        return None
    return {
        "integro": bool(getattr(timestamp, "intact", False)),
        "criptograficamente_valido": bool(getattr(timestamp, "valid", False)),
        "confiavel": bool(getattr(timestamp, "trusted", False)),
        "data_hora": _iso(getattr(timestamp, "timestamp", None)),
    }


def _validate_signature(embedded_sig, allow_fetching=True):
    context = criar_contexto_validacao(
        allow_fetching=allow_fetching,
        other_certs=getattr(embedded_sig, "other_embedded_certs", []),
    )
    sig_type = str(getattr(embedded_sig, "sig_object_type", ""))
    kwargs = {}
    if context is not None:
        kwargs["signer_validation_context"] = context
        kwargs["ts_validation_context"] = context
    if "DocTimeStamp" in sig_type:
        if context is not None:
            status = validate_pdf_timestamp(embedded_sig, validation_context=context)
        else:
            status = validate_pdf_timestamp(embedded_sig)
    else:
        status = validate_pdf_signature(embedded_sig, **kwargs)
    return status, context


def verificar_pdf(source, allow_fetching=True):
    if isinstance(source, (bytes, bytearray)):
        stream = io.BytesIO(source)
    else:
        stream = source
    stream.seek(0)
    reader = PdfFileReader(stream)
    embedded = list(collect_embedded_signatures(reader))
    signatures = []
    for index, sig in enumerate(embedded, start=1):
        cert = sig.signer_cert
        base = {
            "indice": index,
            "campo": getattr(sig, "field_name", None),
            "tipo_objeto": str(getattr(sig, "sig_object_type", "/Sig")),
            "data_hora_declarada": _iso(getattr(sig, "self_reported_timestamp", None)),
            "certificado": certificado_para_dict(cert),
            "certificados_incorporados": [
                certificado_para_dict(item)
                for item in getattr(sig, "other_embedded_certs", [])
            ],
        }
        try:
            status, context = _validate_signature(sig, allow_fetching=allow_fetching)
            integrity = bool(getattr(status, "intact", False))
            crypto_valid = bool(getattr(status, "valid", False))
            trusted = bool(getattr(status, "trusted", False))
            modification_level = _enum_name(
                getattr(status, "modification_level", None)
            )
            docmdp_ok = getattr(status, "docmdp_ok", None)
            warnings = []
            if docmdp_ok is False:
                warnings.append(
                    "A assinatura permanece criptograficamente íntegra, mas foram detectadas "
                    "alterações posteriores incompatíveis com a política de certificação do "
                    "documento. Revise o arquivo antes de confiar nele."
                )
            base.update({
                "validacao_executada": True,
                "integridade_criptografica": integrity,
                "assinatura_criptograficamente_valida": crypto_valid,
                "cadeia_confiavel": trusted,
                "resultado_geral_pyhanko": bool(getattr(status, "bottom_line", False)),
                "algoritmo_digest": getattr(status, "md_algorithm", None),
                "mecanismo_assinatura": getattr(status, "pkcs7_signature_mechanism", None),
                "problema_confianca": _enum_name(getattr(status, "trust_problem_indic", None)),
                "cobertura": _enum_name(getattr(status, "coverage", None)),
                "nivel_modificacao": modification_level,
                "politica_modificacao_ok": docmdp_ok,
                "avisos": warnings,
                "cadeia_validacao": _validation_path(status),
                "revogacao": _revocation(status, allow_fetching, context),
                "timestamp": _timestamp_status(status),
            })
        except Exception as exc:
            base.update({
                "validacao_executada": False,
                "integridade_criptografica": None,
                "assinatura_criptograficamente_valida": None,
                "cadeia_confiavel": False,
                "resultado_geral_pyhanko": False,
                "erro_validacao": f"{type(exc).__name__}: {exc}",
                "revogacao": {
                    "consultas_online_habilitadas": bool(allow_fetching),
                    "consulta_realizada": False,
                    "respostas_ocsp_obtidas": 0,
                    "listas_crl_obtidas": 0,
                    "revogado": None,
                    "estado": "nao_consultada" if allow_fetching else "desabilitada",
                    "conclusao": (
                        "Não foi possível realizar a consulta de revogação."
                        if allow_fetching
                        else "As consultas online de revogação estão desabilitadas."
                    ),
                },
            })
        signatures.append(base)
    if not signatures:
        result_code = "sem_assinaturas"
    elif all(item.get("resultado_geral_pyhanko") is True for item in signatures):
        result_code = "todas_aprovadas_tecnicamente"
    elif any(item.get("integridade_criptografica") is False for item in signatures):
        result_code = "falha_de_integridade"
    else:
        result_code = "requer_atencao"
    return {
        "assinaturas_encontradas": len(signatures),
        "resultado_tecnico": result_code,
        "assinaturas": signatures,
        "aviso": LEGAL_NOTICE,
        "observacao_revogacao": (
            "A ausência de revogação detectada não equivale a uma garantia de não revogação quando "
            "OCSP/CRL não puderam ser consultados ou quando a política de validação não produzir evidência conclusiva."
        ),
    }
